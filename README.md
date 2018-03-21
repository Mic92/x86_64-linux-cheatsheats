# x86_64-linux cheatsheats

Plain files for syscalls, errnos, signals, registers, x86_64 instructions

For use with [cheat](https://github.com/chrisallenlane/cheat):

```console
$ export CHEATPATH=$CHEATPATH:/path/to/this/repo/pages
$ cheat syscalls
$ cheat registers
$ cheat errno
$ cheat EPERM
$ cheat instructions
$ cheat ADD
$ cheat signals
$ cheat SIGHUP
```

## Introspect libc

```
python3 libc.py repl
Type help or ? to list commands.
> print MAP_FAILED
0xffffffffffffffff
> print PROT_WRITE|PROT_READ
3
> type MAP_FAILED
void*
> type memcmp
int (void const*, void const*, unsigned long)
> addr &errno
0x7f3cb86b3fe0
> size "struct timeval"
16
> offset "struct timeval" "tv_usec"
8
> quit
```
