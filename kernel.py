#!/usr/bin/env python3

import os
import sys
import subprocess
import tempfile
import cmd
import platform
import shutil
import shlex
from pathlib import Path

KERNEL_HEADER = """
#include <linux/perf_event.h>
#include <linux/sched.h>
#include <linux/module.h>
#include <linux/kvm_host.h>
MODULE_LICENSE("gpl");
"""


def usage():
    print(
        "USAGE: %s repl|size|print|all|symbols|offset|members" % sys.argv[0],
        file=sys.stderr)
    return 0

KERNEL_DIR = os.environ.get("KERNEL_DIR", f"/lib/modules/{platform.release()}/build")
ROOT = Path(__file__).parent


class KernelModule():
    def __init__(self, content: str) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.build_directory = Path(self.temp.name)
        with open(self.build_directory.joinpath("inspect.c"), "w+") as f:
            f.write(content)

        makefile_path = self.build_directory.joinpath("Makefile")
        with open(makefile_path, "w+") as makefile:
            makefile.write("obj-m += inspect.o\n")
            makefile.write("EXTRA_CFLAGS=-g\n")
            makefile.write("KBUILD_VERBOSE=0\n")

    def build(self) -> Path:
        cmd = ["make", "-s", "-C", KERNEL_DIR, f"M={self.build_directory}"]
        subprocess.check_call(cmd)
        return self.build_directory.joinpath("inspect.ko")

    def __enter__(self) -> Path:
        return self.build()

    def __exit__(self, type, value, traceback):
        self.temp.cleanup()


def main(args):
    if len(args) < 2 or args[1] == "-h" or args[1] == "--help":
        usage()
        return 1
    s = Shell()
    s.args = sys.argv[2:]
    s.onecmd(sys.argv[1])


def parse(arg):
    return tuple(shlex.split(arg))


class Shell(cmd.Cmd):
    intro = 'Type help or ? to list commands.\n'
    prompt = '> '

    def precmd(self, line):
        self.args = parse(line)
        if len(self.args) > 1:
            self.args = self.args[1:]
        return line

    def do_size(self, _):
        """
        print sizeof(expression)
        """
        if len(self.args) < 1:
            print("USAGE: %s print-size expr" % sys.argv[0], file=sys.stderr)
            return 1
        content = (KERNEL_HEADER + f"size_t size = sizeof({self.args[0]});")
        with KernelModule(content) as module:
            subprocess.check_call(["gdb", module, "-batch", "-ex", "p size", "-ex", "quit"])

    do_s = do_size

    def do_print(self, _):
        if len(self.args) < 1:
            print(
                "USAGE: %s print constant" % sys.argv[0],
                file=sys.stderr)
            return 1
        content = (KERNEL_HEADER +
                   f"typeof({self.args[0]}) VAL = {self.args[0]};")
        with KernelModule(content) as module:
            subprocess.check_call(["gdb", module, "-batch", "-ex", "p VAL", "-ex", "quit"])

    do_p = do_print

    def do_offset(self, _):
        """
        print offsetof(struct, member)
        """
        if len(self.args) < 2:
            print(
                "USAGE: %s offset struct member" % sys.argv[0],
                file=sys.stderr)
            return 1
        content = (KERNEL_HEADER +
                   f"size_t OFFSET = __builtin_offsetof({self.args[0]}, {self.args[1]});")
        with KernelModule(content) as module:
            subprocess.check_call(["gdb", module, "-batch", "-ex", "p OFFSET", "-ex", "quit"])

    do_o = do_offset

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
