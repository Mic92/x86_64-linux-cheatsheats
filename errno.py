#!/usr/bin/env python3
import os


def main():
    with open("pages/errno", "w") as f:
        for k, v in sorted(os.errno.errorcode.items()):
            name = os.strerror(k)
            content = "{:>3} {:>15} {}\n".format(k, v, name)
            f.write(content)
            try:
                with open(f"pages/{v}", "w") as f2:
                    f2.write(content)
                    os.symlink(f"{v}", f"pages/{v.lower()}")
            except FileExistsError:
                pass


if __name__ == '__main__':
    main()
