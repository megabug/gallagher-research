#!/usr/bin/env python3

import crcmod
import hexdump

import itertools
import socket
import struct
import sys
import time


def prefix(s, p):
    return '\n'.join('%s%s' % (p, l) for l in s.splitlines())


def indent(s, n=3, tab=False):
    return prefix(s, ('\t' if tab else ' ') * n)


def nth(iterable, n, default=None):
    return next(itertools.islice(iterable, n, None), default)


def make_crc():
    return crcmod.Crc(0x11021, 0)


def lcg(m, a, s):
    while True:
        s = ((s * m) + a) & 0xff
        yield s


def primes():
    n = 2
    while True:
        if all(n % i for i in range(2, n - 1)):
            yield n
        n += 1


CDXIV_FROM_CONTROLLER_COMMANDS = {
    0x07: 'Deny Mifare',
    0x08: 'Deny 125',
    0x0a: 'Enable admin card',
    0x0b: 'Use Mifare extended data format',
    0x0c: "Use high security",
    0x0d: "Don't use high security",
    0x0e: 'Use CSN',
    0x0f: "Don't use CSN",
    0x10: 'Stop buzzer',
    0x11: 'Start buzzer',
    0x18: 'Granted',
    0x19: 'Denied',
    0x21: 'Red LED on',
    0x22: 'Green LED off',
    0x23: 'Red LED off',
    0x24: 'Green LED on',
    0x49: 'Not secure',
    0x4a: 'Hide over bell',
    0x4b: 'Hide under bell',
    0x58: 'Fail',
    0x59: 'Secure',
    0x5a: 'Show over bell',
    0x5b: 'Show under bell',
    0x81: 'Set secure access',
    0x82: 'PIN only',
    0x83: 'Free access',
    0x8a: 'Show wait & failure',
    0x8f: 'Flash all',
    0x90: 'Show default',
    0x91: 'Ask for PIN',
    0x92: 'Display wrong PIN',
    0x93: 'Request second card',
    0x95: 'Flash over bell & under bell & card, show bell',
    0x96: 'Flash over bell & under bell & keypad, show bell',
    0x97: 'Flash bell, start alarm',
    0x98: 'Display set failed',
    0x9f: 'Display standby',
    0xa3: 'Keystroke ACK',
    0xa5: 'Beep',
    0xb1: 'Config MF key? 1',
    0xc0: 'Config MF key? 2',
    0xd5: 'Config MF key? 3',
    0xe0: 'Config MF key? 0 nibble',
    0xe1: 'Config MF key? 1 nibble',
    0xe2: 'Config MF key? 2 nibble',
    0xe3: 'Config MF key? 3 nibble',
    0xe4: 'Config MF key? 4 nibble',
    0xe5: 'Config MF key? 5 nibble',
    0xe6: 'Config MF key? 6 nibble',
    0xe7: 'Config MF key? 7 nibble',
    0xe8: 'Config MF key? 8 nibble',
    0xe9: 'Config MF key? 9 nibble',
    0xea: 'Config MF key? A nibble',
    0xeb: 'Config MF key? B nibble',
    0xec: 'Config MF key? C nibble',
    0xed: 'Config MF key? D nibble',
    0xee: 'Config MF key? E nibble',
    0xef: 'Config MF key? F nibble',
    0xff: 'Heartbeat'
}

CARD_TYPES = {
    0x01: '26-bit HID',
    0x02: '37-bit HID',
    0x03: 'Motorola',
    0x04: 'EM (Deister)',
    0x05: 'CasiRusco',
    0xf5: 'Facility code list?',
    0xf7: 'Mifare extended data format',
    0xf8: 'Mifare enhanced security',
    0xfa: 'Data low',
    0xfb: 'Data high',
    0xfc: 'CardKey',
    0xfd: 'Third party',
    0xfe: 'Cardax magstripe',
    0xff: 'Cardax Prox',
}

DEVICE_TYPES = {
    0x00: 'Controller 5000',
    0x01: 'Strike Controller',
    0x02: 'Prox IDT',
    0x03: 'Prox',
    0x04: 'Magstripe IDT',
    0x05: 'Magstripe',
    0x06: 'URI',
    0x07: 'I/O Board',
    0x08: 'Input Board',
    0x09: 'Relay Board',
    0x0a: 'Intercom',
    0x0b: 'Camera_0',
    0x0c: 'Mifare IDT',
    0x0d: '125 IDT',
    0x0e: '8 Door Interface',
    0x0f: 'Controller 3000',
    0x32: '8Input/4Output Interface',
    0x33: '8Input Interface',
    0x34: '8Output Interface',
    0x35: 'Stoval Reader',
    0x36: 'GBUS URI',
    0x37: '16Input/16Output Interface',
    0x38: 'GBUS URI Wiegand',
    0x39: 'Aperio Unit',
    0x3a: 'RAT',
    0x3b: 'Fence Controller',
    0x3d: 'Controller 5000 GL',
    0x3e: 'Controller 6000',
    0x3f: 'Controller 6000 8R',
    0x40: 'Controller 6000 4R',
    0x41: 'H-BUS Card Reader',
    0x42: 'H-BUS Terminal',
    0x4f: 'H-BUS Alarms Terminal',
    0x43: 'Sensor Device',
    0x44: 'Controller 6000 4H',
    0x45: 'Controller 6000 8H',
    0x46: 'H-BUS Taut Wire Sensor',
    0x47: 'F22 Fence Controller',
    0x4a: 'H-BUS IO 8 In 2 Out',
    0x4b: 'H-BUS IO 16 In 16 Out',
    0x4c: 'H-BUS IO 8 In 4 Out',
    0x4d: 'H-BUS IO 8 In',
    0x49: 'RSI Device',
    0x4e: 'OSDP Device',
    0x50: 'F31 Fence Controller',
    0x51: 'F32 Fence Controller',
    0x52: 'F41 Fence Controller',
    0x53: 'F42 Fence Controller',
    0x54: 'H-BUS Contact Card Reader',
    0x55: 'Class 5 End-of-Line Module',
}


def show_packet(opcode, data):
    if not opcode:
        assert not len(data) % 4
        return ('Ident: ' + ', '.join('v%d.%02d//b%d' % struct.unpack('!BBH', data[i:i+4]) for i in range(0, len(data), 4)))

    if opcode == 1:
        assert data
        if not data[0]:
            assert len(data) == 2
            r = 'invalid packet?, opcode = 0x%02X' % data[1]
        elif data[0] == 1:
            r = 'bad packet?, packet?:\n' + indent(hexdump.hexdump(data[1:], 'return'))
        elif data[0] == 2:
            assert len(data) == 3
            r = 'wrong length?, opcode = 0x%02X, length = %d' % (data[1], data[2])
        elif data[0] == 3:
            r = 'data underflow?'
            if len(data) > 1:
                r += ':\n' + indent(hexdump.hexdump(data[1:], 'return'))
        else:
            assert False

        return 'Notification of invalid packet: ' + r

    if opcode == 2:
        assert data
        r = 'Diagnostic: test type = %d' % data[0]
        if len(data) > 1:
            r += ', rest:\n' + indent(hexdump.hexdump(data[1:], 'return'))
        return r

    if opcode == 3:
        assert not len(data) % 2
        r = 'Beep:'
        return ('Beep: ' + ', '.join('len %d pitch %d' % struct.unpack('!BB', data[i:i+2]) for i in range(0, len(data), 2)))

    if opcode == 4:
        assert data
        r = 'Display: flag = %d, data:\n' % data[0]
        r += indent(hexdump.hexdump(data, 'return'))
        return r

    if opcode == 5:
        assert len(data) == 2
        return 'I/O event: number = %d, %s' % (data[0], 'closed' if data[1] else 'open')

    if opcode == 6:
        assert len(data) == 6
        val_id, val_val = struct.unpack('!HI', data)
        return 'Set/notify configuration: 0x%04X = 0x%08X' % (val_id, val_val)

    if opcode == 7:
        assert len(data) == 2
        val_id = struct.unpack('!H', data)
        return 'Get configuration: 0x%04X' % val_id

    if opcode == 8:
        assert len(data) >= 2 and not len(data) % 2
        return 'Get character bitmap(s): ' + ', '.join('0x%04X' % struct.unpack('!H', data[i:i+2]) for i in range(0, len(data), 2))

    if opcode == 9:
        assert len(data) >= 2
        r = 'Character bitmap: record 0x%04X, bitmap:\n' % struct.unpack('!H', data[:2])[0]
        r += indent(hexdump.hexdump(data[2:], 'return'))
        return r

    if opcode == 0xa:
        assert len(data) == 2
        return 'Initial download data: unknown1 0x%02X, unknown2 0x%02X' % tuple(data)

    if opcode == 0xb:
        return 'Continuing download data: data:\n' + indent(hexdump.hexdump(data, 'return'))

    if opcode == 0xc:
        r = ''

        if data[0] & 0x01:
            r += 'Alarm history / Power too low'
        if data[0] & 0x02:
            r += 'Alarm active / Power too high'
        if data[0] & 0x04:
            r += 'Front tampered'
        if data[0] & 0x08:
            r += 'Rear tampered'
        if data[0] & 0x10:
            r += 'Tampered'

        for i, d in enumerate(data[1:]):
            if r:
                r += '\n'
            r += 'Input %d: change %d, state %d' % (i, d >> 4, d & 0xf)

        return 'Input status:\n' + indent(r)

    if opcode == 0xd:
        assert len(data) == 2
        return 'Key press: key 0x%02X%s, reader %d' % (data[0], ' (%s)' % chr(data[0]) if 0x20 <= data[0] < 0x7f else '', data[1])

    if opcode == 0xe:
        assert len(data) >= 2
        return 'Unit event: event ID %d, priority %r, msg %r' % (data[0], {0: 'event', 1: 'warning', 2: 'failure'}.get(data[1], str(data[1])), data[2:].decode('iso-8859-1'))

    if opcode == 0xf:
        assert len(data) >= 1
        r = 'Card data (old packet): reader %d, data:\n' % data[0]
        r += indent(hexdump.hexdump(data[1:], 'return'))
        return r

    if opcode == 0x10:
        assert len(data) == 3
        n = (data[0] << 16) | (data[1] << 8) | data[2]
        return 'Request archive: thing = %d' % n

    if 0x11 <= opcode <= 0x13:
        assert data
        r = 'Localbus message:\n'
        r += indent(hexdump.hexdump(data, 'return'))
        return r

    if opcode == 0x14:
        return 'Unknown event thing'

    if opcode == 0x15:
        assert len(data) == 2
        return 'CDXIV command: reader %d, command 0x%02X (%s)' % (data[0], data[1], CDXIV_FROM_CONTROLLER_COMMANDS.get(data[1], 'unknown'))

    if opcode == 0x16:
        assert len(data) >= 4
        #assert struct.unpack('!H', data[-2:])[0] == 8 * (len(data) - 4)

        r = 'Card data: reader %d, type 0x%02X (%s), data:\n' % (data[0], data[1], CARD_TYPES.get(data[1], 'unknown'))
        r += indent(hexdump.hexdump(data[2:-2], 'return'))
        r += 'last 2 %04X' % struct.unpack('!H', data[-2:])
        return r

    if opcode == 0x17:
        assert data
        r = ''
        for i, d in enumerate(data[::-1]):
            for j in range(8):
                r += 'Reader %d: %s\n' % (i * 8 + j, 'offline' if d & (1 << j) else 'online / N/A')

        return 'URI reader status:\n' + indent(r)

    if opcode == 0x21:
        assert len(data) <= 4
        r = ''
        for i, d in enumerate(data):
            for j in range(4):
                v = {0: 'online', 1: 'offline', 2: 'unknown reader status', 3: 'unknown'}[(d >> (j * 2)) & 3]
                r += 'Reader %d: %s\n' % (i * 4 + j, v)

        return 'Reader status:\n' + indent(r)

    # TODO: these are HBUS?:

    if opcode == 0x22:
        assert len(data) == 10
        return 'LEDPattern: unknown = 0x%02X, colour A = %d, duration A = %d, colour B = %d, duration B = %d, repeat count = %d, gap time = %d' % struct.unpack('!BBHBHBH', data)

    if opcode == 0x23:
        return 'Play: tune = %r' % data.decode('iso-8859-1')

    if data:
        r = 'Unknown packet type 0x%02X:\n' % opcode
        r += indent(hexdump.hexdump(data, 'return'))
    else:
        r = 'Unknown packet type %d' % opcode
    return r


class Device(object):

    def __init__(self, addr):
        self.addr = addr
        self.type = None
        self.last_poll_recv = time.time()
        self.next_seq = 0
        self.in_flight = 0

        self.reset_lcg()
        self.poss_lcg_params = set()

    def reset_lcg(self):
        self.next_seeds = {True: [None] * 4, False: [None] * 4}
        self.poss_lcg_params = {(0x43, 0x11)}
        self.next_lcg_params = [None, None]
        self.last_resp_seq = None

    def handle_frame(self, frame):
        r = ''

        #print('in: %r' % self.__dict__)

        is_poll = bool(frame[0] & 0x40)
        assert bool(frame[0] & 0x80) != is_poll
        assert frame[0] & 0xf == 0x4 if is_poll else 0xe
        seq = (frame[0] >> 4) & 0x3

        if frame[1] != 0xfe:
            if frame[1] != self.type:
                assert self.type in {0xfe, None}
                r += 'Device found: 0x%02X (%s)\n' % (frame[1], DEVICE_TYPES.get(frame[1], 'unknown'))
                self.type = frame[1]
        elif self.type != 0xfe:
            if self.type is not None:
                r += 'Device lost\n'
            self.type = frame[1]
            self.reset_lcg()

        b = frame[3:]

        if len(self.poss_lcg_params) != 1 and self.next_seeds[is_poll][seq] is not None:
            r += 'Guessing LCG\n'
            ps = set()
            for m in PRIMES:
                for a in PRIMES:
                    if nth(lcg(m, a, self.next_seeds[is_poll][seq]), len(b) - 1) == b[-1]:
                        ps.add((m, a))
            if not self.poss_lcg_params:
                self.poss_lcg_params = ps
            else:
                self.poss_lcg_params &= ps
            if len(self.poss_lcg_params) == 1:
                r += 'Found LCG: %r\n' % (list(self.poss_lcg_params)[0],)

        if len(self.poss_lcg_params) == 1 and self.next_seeds[is_poll][seq] is not None:
            p = list(self.poss_lcg_params)[0] + (self.next_seeds[is_poll][seq],)
            b = bytes(x ^ y for x, y in zip(b, lcg(*p)))

            if not b[-1]:
                b = b[:-1]
                if is_poll:
                    r += self.handle_poll(b, seq)
                    self.last_poll_recv = time.time()
                    self.in_flight += 1
                else:
                    r += self.handle_response(b, seq)
                    self.last_resp_seq = seq
                    self.in_flight -= 1
            else:
                r += 'Bad unLCG %s:\n' % ('poll' if is_poll else 'response')
                r += indent(hexdump.hexdump(frame, 'return'))
        else:
            r += 'Unable to unLCG %s:\n' % ('poll' if is_poll else 'response')
            r += indent(hexdump.hexdump(frame, 'return'))

        if is_poll:
            self.next_seeds[False][seq] = frame[2]
        else:
            self.next_seq = (seq + 1) % 4
            self.next_seeds[True][self.next_seq] = frame[2]

        #print('out: %r' % self.__dict__)
        return r

    def poll(self, packets):
        if self.type is None or self.in_flight >= 2:
            print('(Device %d resetting for poll)' % self.addr)
            print()
            #time.sleep(1)
            self.type = 0xfe
            self.in_flight = 0
            self.reset_lcg()
            self.next_seq = 0
            self.next_seeds[True][self.next_seq] = 0

        b = bytes(x ^ y for x, y in zip(packets + bytes([0]), lcg(*list(self.poss_lcg_params)[0] + (self.next_seeds[True][self.next_seq],))))

        return bytes([0x44 | (self.next_seq << 4), self.type, 3]) + b


class PassiveDevice(Device):

    def handle_poll(self, packets, seq):
        r = ''

        if packets:
            r += 'Poll (%d):\n' % seq
            #return r + indent(hexdump.hexdump(packets, 'return')) # TODO remove
            for m in range(2):
                n = 0
                while n < len(packets):
                    opcode = packets[n]
                    l = packets[n + 1]

                    if not m and l > len(packets) - n - 2:
                        r += 'Bad packet(s) in frame:\n' + indent(hexdump.hexdump(packets, 'return')) + '\n'
                        return r
                    data = packets[n+2:n+2+l]

                    if m:
                        if opcode == 6:
                            val_id, val_val = struct.unpack('!HI', data)
                            if val_id in {3, 4}:
                                self.next_lcg_params[0 if val_id == 3 else 1] = val_val

                        r += indent(show_packet(opcode, data)) + '\n'

                    n += l + 2

        return r

    def handle_response(self, packets, seq):
        r = ''

        global respd
        respd += 1

        if packets:
            r += 'Response (%d):\n' % seq
            for m in range(2):
                n = 0
                while n < len(packets):
                    opcode = packets[n]
                    l = packets[n + 1]

                    if not m and l > len(packets) - n - 2:
                        r += 'Bad packet(s) in frame:\n' + indent(hexdump.hexdump(packets, 'return')) + '\n'
                        return r
                    data = packets[n+2:n+2+l]

                    if m:
                        r += indent(show_packet(opcode, data)) + '\n'

                    n += l + 2

        if self.next_lcg_params[0] is not None:
            self.poss_lcg_params = {(self.next_lcg_params[0], list(self.poss_lcg_params)[0][1])}
        if self.next_lcg_params[1] is not None:
            self.poss_lcg_params = {(list(self.poss_lcg_params)[0][0], self.next_lcg_params[1])}

        self.next_lcg_params = [None, None]

        return r


PRIMES = list(itertools.takewhile(lambda p: p < 0x100, primes()))[1:]
assert len(PRIMES) == 0x35

STX = 0x02
ETX = 0x03
DLE = 0x10

MODE_IDLE = 0
MODE_FRAME = 1
MODE_FRAME_ESCAPED = 2
MODE_CRC_1 = 3
MODE_CRC_2 = 4


BUS_MASTER = True
POLL_INTERVAL = 0.1

devices = {}

devices[0] = PassiveDevice(0)
devices[1] = PassiveDevice(1)
devices[2] = PassiveDevice(2)


def handle_frame(frame):
    addr = frame[0] & 0xf
    assert (frame[0] >> 4) == 1

    if addr not in devices:
        devices[addr] = PassiveDevice(addr)

    device = devices[addr]

    if device.type is not None:
        t = '0x%02X (%s)' % (device.type, DEVICE_TYPES.get(device.type, 'unknown'))
    else:
        t = 'unseen'

    r = device.handle_frame(frame[1:])
    if r:
        print('Device %d (%s):' % (addr, t))
        print(indent(r.rstrip('\n')))
        print()


def frame_escape(b):
    r = b''
    for c in b:
        if STX <= c <= ETX or c == DLE:
            r += bytes([DLE])
        r += bytes([c])
    return r


def main(argv):
    global respd

    io = sys.stdin.buffer if argv[1] == '-' else socket.create_connection(argv[1].split(':'))

    br = 0
    mode = MODE_IDLE
    crc = make_crc()
    nn = 0
    while True:
        if argv[1] != '-' and BUS_MASTER:
            # TODO: this ordering of polling is broken
            es = {addr: time.time() - device.last_poll_recv for addr, device in devices.items()}
            if all(e >= POLL_INTERVAL for e in es.values()):
                device = devices[max(es, key=lambda k: es[k])]
                out = b''
                frame = bytes([device.addr | 0x10]) + device.poll(out)
                wire = bytes([STX]) + frame_escape(frame) + bytes([ETX])
                out_crc = make_crc()
                out_crc.update(wire)
                wire += out_crc.digest()[::-1]
                io.sendall(wire)
                handle_frame(frame)

            io.settimeout(POLL_INTERVAL / 100) # TODO ugh
            try:
                c = io.recv(1)
            except socket.timeout:
                continue
        else:
            c = io.read(1)

        if not c:
            break
        c = c[0]

        crc.update(bytes([c]))

        if mode == MODE_IDLE:
            if c == STX:
                frame = b''
                crc = make_crc()
                crc.update(bytes([c]))
                mode = MODE_FRAME
        elif mode == MODE_FRAME:
            if c == DLE:
                mode = MODE_FRAME_ESCAPED
            elif c == ETX:
                mode = MODE_CRC_1
            else:
                frame += bytes([c])
        elif mode == MODE_FRAME_ESCAPED:
            frame += bytes([c])
            mode = MODE_FRAME
        elif mode == MODE_CRC_1:
            mode = MODE_CRC_2
        elif mode == MODE_CRC_2:
            if not crc.crcValue:
                handle_frame(frame)
            else:
                print('Dropping frame at %d: bad CRC:' % br)
                print(indent(hexdump.hexdump(frame, 'return')))
                print()

            mode = MODE_IDLE

        br += 1


if __name__ == '__main__':
    main(sys.argv)
