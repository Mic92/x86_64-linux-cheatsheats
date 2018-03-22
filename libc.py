#!/usr/bin/env python3

import os
import subprocess
import sys
import tempfile
import shlex
import cmd
from collections import defaultdict

C_HEADER = """
#define _GNU_SOURCE 

extern "C" {
#include <elf.h>
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
    print(
        "USAGE: %s repl|size|print|all|symbols|offset" % sys.argv[0],
        file=sys.stderr)
    return 0


def execute(f):
    try:
        exe = tempfile.NamedTemporaryFile(delete=True)
        exe.close()
        subprocess.check_call(
            ["c++", "-std=c++11", "-w", "-o", exe.name, "-x", "c++", f.name])
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
    s = Shell()
    s.args = sys.argv[2:]
    s.onecmd(sys.argv[1])


def parse(arg):
    return tuple(shlex.split(arg))


def gdb(arg, command):
    f = tempfile.NamedTemporaryFile(mode="w+")
    f.write(C_HEADER + """int main() {
            %s a;
            printf("%%p", &a);
    }""" % arg)
    f.flush()
    subprocess.check_call(
        ["c++", "-std=c++11", "-g", "-o", "/tmp/main", "-w", "-x", "c++", f.name])
    return subprocess.check_output(["gdb", "--nh", "-batch", "-ex", command, "/tmp/main"]).decode("utf-8")


class Shell(cmd.Cmd):
    intro = 'Type help or ? to list commands.\n'
    prompt = '> '

    def precmd(self, line):
        self.args = parse(line)
        if len(self.args) > 1:
            self.args = self.args[1:]
        return line

    def do_print(self, _):
        """
        print expression
        """
        if len(self.args) < 1:
            print("USAGE: %s print expr" % sys.argv[0], file=sys.stderr)
            return 1
        f = tempfile.NamedTemporaryFile(mode="w+")
        f.write(
            CXX_HEADER +
            "int main(int argc, char** argv) { std::cout << \"0x\" << std::hex << (%s) << std::endl; }"
            % self.args[0])
        f.flush()
        execute(f)

    do_p = do_print
    default = do_print

    def do_size(self, _):
        """
        print sizeof(expression)
        """
        if len(self.args) < 1:
            print("USAGE: %s print-size expr" % sys.argv[0], file=sys.stderr)
            return 1
        f = tempfile.NamedTemporaryFile(mode="w+")
        f.write(CXX_HEADER +
                "int main() { std::cout << \"0x\" << std::hex << sizeof(%s) << std::endl; }" %
                (self.args[0]))
        f.flush()
        execute(f)

    do_s = do_size

    def do_addr(self, _):
        """
        print pointer value
        """
        if len(self.args) < 1:
            print("USAGE: %s addr expr" % sys.argv[0], file=sys.stderr)
            return 1
        f = tempfile.NamedTemporaryFile(mode="w+")
        f.write(CXX_HEADER + "int main() { printf(\"%%p\\n\", %s); }" %
                (self.args[0]))
        f.flush()
        execute(f)

    do_a = do_addr

    def do_type(self, _):
        """
        print type of expression
        """
        if len(self.args) < 1:
            print("USAGE: %s type" % sys.argv[0], file=sys.stderr)
            return 1
        f = tempfile.NamedTemporaryFile(mode="w+")
        f.write(
            CXX_HEADER +
            "int main() { std::cout << type_name<decltype(%s)>() << std::endl; }"
            % (self.args[0]))
        f.flush()
        execute(f)

    do_t = do_type

    def do_offset(self, _):
        """
        print offsetof(struct, member)
        """
        if len(self.args) < 2:
            print(
                "USAGE: %s offset struct member" % sys.argv[0],
                file=sys.stderr)
            return 1
        f = tempfile.NamedTemporaryFile(mode="w+")
        f.write(CXX_HEADER +
                "int main() { std::cout << \"0x\" << std::hex << offsetof(%s, %s) << std::endl; }" %
                (self.args[0], self.args[1]))
        f.flush()
        execute(f)

    do_o = do_offset

    def do_symbols(self, _):
        """
        Print symbols
        """
        f = tempfile.NamedTemporaryFile(mode="w+")
        f.write(C_HEADER + "int main() {}")
        f.flush()
        subprocess.check_call(["cpp", f.name])

    def do_all(self, _):
        """
        Print libc header with all macros/definitions
        """
        f = tempfile.NamedTemporaryFile(mode="w+")
        f.write(C_HEADER + "int main() {}")
        f.flush()
        if subprocess.check_output(["cpp", "--version"]).startswith(b"clang"):
            subprocess.check_call(["cpp", "-frewrite-includes", f.name])
        else:
            subprocess.check_call(["cpp", "-fdirectives-only", f.name])

    def do_members(self, _):
        """
        Print type information using gdb. For structs print members
        """
        out = gdb(self.args[0], "ptype %s" % self.args[0])
        print(out.replace("type = ", ""))

    def do_gdboffset(self, _):
        """
        Print offset calculated by gdb
        """
        if len(self.args) < 2:
            print(
                "USAGE: %s offset struct member" % sys.argv[0],
                file=sys.stderr)
            return 1
        print(gdb(self.args[0], f"print &(({self.args[0]} *) 0)->{self.args[1]}"))
 
    def do_exit(self, _):
        """
        Exit
        """
        return True

    def do_quit(self, _):
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
