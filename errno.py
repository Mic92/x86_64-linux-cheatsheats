#!/usr/bin/env python3
import os


def main():
    with open("pages/errno", "w") as f:
        for k, v in sorted(os.errno.errorcode.items()):
            f.write("{:>3} {:>15} {}\n".format(k, v, os.strerror(k)))


if __name__ == '__main__':
    main()
