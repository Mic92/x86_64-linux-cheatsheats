#!/usr/bin/env python3

import os
import subprocess
import sys
import tempfile
import shlex
import cmd

C_HEADER = """
#define _GNU_SOURCE 

extern "C" {
#include <asm/mman.h>
#include <ctype.h>
#include <dirent.h>
#include <dlfcn.h>
#include <errno.h>
#include <execinfo.h>
#include <fcntl.h>
#include <glob.h>
#include <grp.h>
#include <ifaddrs.h>
#include <langinfo.h>
#include <limits.h>
#include <linux/falloc.h>
#include <linux/fs.h>
#include <linux/if.h>
#include <linux/input.h>
#include <linux/magic.h>
#include <linux/netlink.h>
#include <linux/quota.h>
#include <linux/reboot.h>
#include <locale.h>
#include <malloc.h>
#include <mqueue.h>
#include <netdb.h>
#include <net/ethernet.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <netpacket/packet.h>
#include <poll.h>
#include <pthread.h>
#include <pty.h>
#include <pwd.h>
#include <resolv.h>
#include <sched.h>
#include <semaphore.h>
#include <shadow.h>
#include <signal.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/epoll.h>
#include <sys/eventfd.h>
#include <sys/file.h>
#include <sys/ioctl.h>
#include <sys/io.h>
#include <sys/ipc.h>
#include <syslog.h>
#include <sys/mman.h>
#include <sys/msg.h>
#include <sys/personality.h>
#include <sys/prctl.h>
#include <sys/ptrace.h>
#include <sys/quota.h>
#include <sys/reboot.h>
#include <sys/reg.h>
#include <sys/resource.h>
#include <sys/sem.h>
#include <sys/sendfile.h>
#include <sys/shm.h>
#include <sys/signalfd.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <sys/swap.h>
#include <sys/syscall.h>
#include <sys/sysctl.h>
#include <sys/sysinfo.h>
#include <sys/time.h>
#include <sys/timerfd.h>
#include <sys/times.h>
#include <sys/types.h>
#include <sys/uio.h>
#include <sys/un.h>
#include <sys/user.h>
#include <sys/utsname.h>
#include <sys/vfs.h>
#include <sys/wait.h>
#include <sys/xattr.h>
#include <termios.h>
#include <time.h>
#include <ucontext.h>
#include <unistd.h>
#include <utime.h>
#include <utmpx.h>
#include <wchar.h>
}
"""

CXX_HEADER = C_HEADER + """
#include <iostream>
#include <type_traits>
#include <typeinfo>
#ifndef _MSC_VER
#   include <cxxabi.h>
#endif
#include <memory>
#include <string>
#include <cstdlib>

template <class T>
std::string
type_name()
{
    typedef typename std::remove_reference<T>::type TR;
    std::unique_ptr<char, void(*)(void*)> own
           (
#ifndef _MSC_VER
                abi::__cxa_demangle(typeid(TR).name(), nullptr,
                                           nullptr, nullptr),
#else
                nullptr,
#endif
                std::free
           );
    std::string r = own != nullptr ? own.get() : typeid(TR).name();
    if (std::is_const<TR>::value)
        r += " const";
    if (std::is_volatile<TR>::value)
        r += " volatile";
    if (std::is_lvalue_reference<T>::value)
        r += "&";
    else if (std::is_rvalue_reference<T>::value)
        r += "&&";
    return r;
}
"""


def usage():
    print("USAGE: %s repl|size|print|all|symbols|offset" % sys.argv[0], file=sys.stderr)
    return 0


def execute(f):
    try:
        exe = tempfile.NamedTemporaryFile(delete=True)
        exe.close()
        subprocess.check_call(
            ["c++", "-w", "-o", exe.name, "-x", "c++", f.name])
        subprocess.check_call([exe.name])
    except subprocess.CalledProcessError:
        pass
    finally:
        try:
            os.unlink(exe.name)
        except FileNotFoundError:
            pass


def main(args):
    if len(args) < 2 or args[1] == "-h" or args[1] == "--help":
        usage()
        return 1
    Shell().onecmd(" ".join(sys.argv[1:]))


def parse(arg):
    'Convert a series of zero or more numbers to an argument tuple'
    return tuple(shlex.split(arg))


class Shell(cmd.Cmd):
    intro = 'Type help or ? to list commands.\n'
    prompt = '> '

    def do_print(self, arg):
        """
        print expression
        """
        args = parse(arg)
        if len(args) < 1:
            print("USAGE: %s print expr" % sys.argv[0], file=sys.stderr)
            return 1
        f = tempfile.NamedTemporaryFile(mode="w+")
        f.write(
            CXX_HEADER +
            "int main(int argc, char** argv) { std::cout << (%s) << std::endl; }"
            % args[0])
        f.flush()
        execute(f)

    do_p = do_print
    default = do_print

    def do_size(self, arg):
        """
        print sizeof(expression)
        """
        args = parse(arg)
        if len(args) < 1:
            print("USAGE: %s print-size expr" % sys.argv[0], file=sys.stderr)
            return 1
        f = tempfile.NamedTemporaryFile(mode="w+")
        f.write(CXX_HEADER +
                "int main() { std::cout << sizeof(%s) << std::endl; }" %
                (args[0]))
        f.flush()
        execute(f)

    do_s = do_size

    def do_addr(self, arg):
        """
        print pointer value
        """
        args = parse(arg)
        if len(args) < 1:
            print("USAGE: %s addr expr" % sys.argv[0], file=sys.stderr)
            return 1
        f = tempfile.NamedTemporaryFile(mode="w+")
        f.write(CXX_HEADER + "int main() { printf(\"%%p\\n\", %s); }" % (args[0]))
        f.flush()
        execute(f)

    do_a = do_addr

    def do_type(self, arg):
        """
        print type of expression
        """
        args = parse(arg)
        if len(args) < 1:
            print("USAGE: %s type" % sys.argv[0], file=sys.stderr)
            return 1
        f = tempfile.NamedTemporaryFile(mode="w+")
        f.write(CXX_HEADER + "int main() { std::cout << type_name<decltype(%s)>() << std::endl; }" % (args[0]))
        f.flush()
        execute(f)

    do_t = do_type

    def do_offset(self, arg):
        """
        print offsetof(struct, member)
        """
        args = parse(arg)
        if len(args) < 2:
            print(
                "USAGE: %s offset struct member" % sys.argv[0],
                file=sys.stderr)
            return 1
        f = tempfile.NamedTemporaryFile(mode="w+")
        f.write(CXX_HEADER +
                "int main() { std::cout << offsetof(%s, %s) << std::endl; }" %
                (args[0], args[1]))
        f.flush()
        execute(f)

    do_o = do_offset

    def do_symbols(self, arg):
        f = tempfile.NamedTemporaryFile(mode="w+")
        f.write(C_HEADER + "int main() {}")
        f.flush()
        subprocess.check_call(["cpp", f.name])

    def do_all(self, arg):
        f = tempfile.NamedTemporaryFile(mode="w+")
        f.write(C_HEADER + "int main() {}")
        f.flush()
        subprocess.check_call(["cpp", "-fdirectives-only", f.name])

    def do_exit(self, arg):
        """
        Exit
        """
        return True

    def do_quit(self, arg):
        """
        Exit
        """
        return True


if len(sys.argv) < 2:
    usage()
    sys.exit(0)
elif sys.argv[1] == "repl":
    Shell().cmdloop()
else:
    sys.exit(main(sys.argv))
