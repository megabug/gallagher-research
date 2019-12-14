#!/usr/bin/env python

import hexdump
import pigpio

import functools
import operator
import sys
import time


def pulses(d, direction):
	ps = []

	l = 162 if direction else 845
	r = 230 if direction else 2500
	a = 1 << 18 if direction else 0
	b = 0 if direction else 1 << 4

	for c in d:
		d = l if c == '1' else 44
		ps += [
			pigpio.pulse(a, b, d),
			pigpio.pulse(b, a, r - d)
		]

	return ps


start_tick = {}
recv = {}

def cb(gpio, level, tick):
	direction = gpio == 17

	if level == pigpio.TIMEOUT:
		if gpio in recv:
			print 'C -> R' if direction else 'R -> C',
			print '|', tick / 1.0e6
			if not len(recv[gpio]) % 8:
				d = ''.join(chr(int(recv[gpio][i:i+8], 2))
					    for i in range(0, len(recv[gpio]),
                                                8))
				hexdump.hexdump(d)
			else:
				print 'Partial:', recv[gpio]

			del start_tick[gpio]
			del recv[gpio]
	elif bool(level) != direction:
		start_tick[gpio] = tick
	elif gpio in start_tick:
		recv.setdefault(gpio, '')
		recv[gpio] += str(int(tick - start_tick[gpio] >= 100))


def go(pig):
	pig.set_mode(4, pigpio.OUTPUT)
	pig.set_mode(17, pigpio.INPUT)
	pig.set_mode(18, pigpio.OUTPUT)
	pig.set_mode(23, pigpio.INPUT)

	pig.callback(17, pigpio.EITHER_EDGE, cb)
	pig.set_watchdog(17, 3)
	pig.callback(23, pigpio.EITHER_EDGE, cb)
	pig.set_watchdog(23, 1)

	binc = lambda x: ('0' * 8 + bin(x)[2:])[-8:]

	if len(sys.argv) >= 1 + 2:
		time.sleep(.2)

		pig.wave_clear()
		p = ([pigpio.pulse(0, 1 << 18, 20000)]
                        if sys.argv[1] == 'from_r' else
                        [pigpio.pulse(1 << 4, 0, 20000)])
		d = sys.argv[1:]
		for i in range(len(d)):
			if d[i] == 'l':
				d[i] = len(d) - 1
		d = [int(x, 16) if isinstance(x, basestring) and len(x) == 2
                        else x for x in d]
		if d[-1] == 'x':
			d[-1] = functools.reduce(operator.xor, d[1:-1])
		print 'Output: %s' % ' '.join('%02x' % x for x in d)
		pig.wave_add_generic(p + pulses(''.join(binc(x) for x in d),
                    sys.argv[1] == 'from_r') + p)
		pig.wave_send_once(pig.wave_create())

	try:
		#time.sleep(.2)
		time.sleep(9e99)
	except KeyboardInterrupt:
		pass


pig = pigpio.pi()
try:
	go(pig)
finally:
	pig.stop()
