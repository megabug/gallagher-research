#!/usr/bin/env python3

import crcmod
import hexdump

import socket
import struct
import sys
import time


def prefix(s, p):
    return '\n'.join('%s%s' % (p, l) for l in s.splitlines())


def indent(s, n=3, tab=False):
    return prefix(s, ('\t' if tab else ' ') * n)


STX = 0x02
ETX = 0x03
DLE = 0x10

MODE_IDLE = 0
MODE_FRAME = 1
MODE_FRAME_ESCAPED = 2
MODE_TRAILER = 3


def handle_frame(frame):
    crc_fn = crcmod.mkCrcFun(0x11EDC6F41, 0, True, 0xFFFFFFFF)
    calc_crc = crc_fn(frame[:-4])
    crc = struct.unpack('!I', frame[-4:])[0]
    assert calc_crc == crc

    to_addr, from_addr, unk1, seq1, seq2, thing = struct.unpack('!HHBBBH',
            frame[:9])

    unk2 = thing >> 9
    length = thing & ((1 << 9) - 1)
    assert length == len(frame[9:]) - 4

    print(('0x%04X -> 0x%04X | sentseq %d nextrecvseq %d | unk1 %02x '
        'unk2 %02x' % (from_addr, to_addr, seq1, seq2, unk1, unk2)))
    print(indent(hexdump.hexdump(frame[:9], 'return')))
    if length:
        print(indent(hexdump.hexdump(frame[9:9+length], 'return')))
    print()


def main(argv):
    io = sys.stdin.buffer if argv[1] == '-' else socket.create_connection(argv[1].split(':'))

    br = 0
    mode = MODE_IDLE
    while True:
        if argv[1] != '-':
            pass
        else:
            c = io.read(1)

        if not c:
            break
        c = c[0]

        if mode == MODE_IDLE:
            if c == STX:
                frame = b''
                mode = MODE_FRAME
            else:
                print('Discarded: %02x' % c)
                print()
        elif mode == MODE_FRAME:
            if c == DLE:
                mode = MODE_FRAME_ESCAPED
            elif c == ETX:
                mode = MODE_TRAILER
            else:
                frame += bytes([c])
        elif mode == MODE_FRAME_ESCAPED:
            frame += bytes([c ^ DLE])
            assert frame[-1] in {DLE, STX, ETX}
            mode = MODE_FRAME
        elif mode == MODE_TRAILER:
            assert c == 0xFF
            handle_frame(frame)
            mode = MODE_IDLE

        br += 1


if __name__ == '__main__':
    main(sys.argv)
