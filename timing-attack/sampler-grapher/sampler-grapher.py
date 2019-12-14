#!/usr/bin/env python3

import json
import os
import sys

from matplotlib.collections import PatchCollection
from matplotlib.patches import Patch, Rectangle
from matplotlib.cm import Paired
import matplotlib.pyplot as plt


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


PREDICTORS = {}

def predictor(f):
    f.color = 'C%d' % len(PREDICTORS)
    PREDICTORS[f.__name__.replace('_', '-').replace('-predictor', '')] = f
    return f


@predictor
def beep_mute_delay_predictor(recvs, last_send_at):
    last_recv_beep = None
    for recv in recvs:
        opcode = recv['recv']['opcode']
        if opcode == 0xa5:
            last_recv_beep = recv
        elif opcode == 0x10:
            return (last_recv_beep is None or
                    recv['at'] - last_recv_beep['at'] >= 50e3 * 1.5)

    return True


@predictor
def red_led_predictor(recvs, last_send_at):
    return any(recv['recv']['opcode'] in {0x21, 0x23} for recv in recvs)


@predictor
def low_recvs_predictor(recvs, last_send_at):
    return len(recvs) <= 3


@predictor
def immediate_gap_predictor(recvs, last_send_at):
    return not recvs or recvs[0]['at'] - last_send_at >= 50e3


@predictor
def high_delay_predictor(recvs, last_send_at):
    return any(recv.get('_delay', 0) >= 50e3 * 3.5 for recv in recvs)


@predictor
def high_rel_delay_predictor(recvs, last_send_at):
    for recv in recvs:
        if '_delay' in recv:
            if abs((recv['_delay'] + 50e3 / 2) % 50e3 - 50e3 / 2) >= 5e3:
                return True
    return False


TESTS = json.load(sys.stdin)

CORRECT_FC = int(sys.argv[1])


for test in TESTS:
    events = sorted(test['runs'], key=lambda e: e['at'])

    print('%dus: %d' % (test['send-wait-time'], len(events)))

    RECVS = [event for event in events if 'recv' in event]
    SENDS = [event for event in events if 'send' in event]

    WIDTH = 15e6

    CNS = {x: Paired(i) for i, x in enumerate(set(recv['recv']['opcode']
        for recv in RECVS))}

    CORRECT_SENDS = [send for send in SENDS if send['send']['fc'] ==
            CORRECT_FC]

    for a, b in zip(RECVS[:-1], RECVS[1:]):
        a['_delay'] = b['at'] - a['at']

    last_send = None
    rs = []
    for predictor in PREDICTORS.values():
        predictor.tps = predictor.tns = predictor.fps = predictor.fns = 0
    for event in events + [{'_dummy': True, 'at': events[-1]['at']}]:
        if 'send' in event or '_dummy' in event:
            if last_send is not None:
                last_send['_width'] = event['at'] - last_send['at']

                for predictor_name, predictor in PREDICTORS.items():
                    if predictor(rs, last_send['at']):
                        last_send.setdefault('_predictors', []).append(
                                predictor)
                        if last_send['send']['fc'] == CORRECT_FC:
                            predictor.tps += 1
                        else:
                            predictor.fps += 1
                    else:
                        if last_send['send']['fc'] == CORRECT_FC:
                            predictor.fns += 1
                        else:
                            predictor.tns += 1

            rs = []
            last_send = event
        elif 'recv' in event:
            rs.append(event)

    NOT_REPEATED_CORRECT_SENDS = []
    for correct_send in CORRECT_SENDS:
        if not NOT_REPEATED_CORRECT_SENDS or (correct_send['at'] -
                NOT_REPEATED_CORRECT_SENDS[-1]['at']) >= 50e3 * 30:
            NOT_REPEATED_CORRECT_SENDS.append(correct_send)

    f = plt.figure(figsize=(30, len(NOT_REPEATED_CORRECT_SENDS)))
    f.suptitle("%dus send wait time, %d repeat(s)" %
            (test['send-wait-time'], test.get('send-repeats', 1)),
            fontsize=16)

    handles=([Patch(color=c, label='0x%02X (%s)' %
        (l, CDXIV_FROM_CONTROLLER_COMMANDS[l]))
        for l, c in sorted(CNS.items())] +
        [Patch(color=predictor.color,
            label=('%s (%d/%.1f%% TP, %d/%.1f%% TN, %d/%.1f%% FP, '
                '%d/%.1f%% FN)' % (
                    predictor_name,
                    predictor.tps, predictor.tps / len(CORRECT_SENDS) * 100,
                    predictor.tns, predictor.tns / (len(SENDS) -
                        len(CORRECT_SENDS)) * 100,
                    predictor.fps, predictor.fps / (len(SENDS) -
                        len(CORRECT_SENDS)) * 100,
                    predictor.fns, predictor.fns / len(CORRECT_SENDS) * 100)))
                    for predictor_name, predictor in PREDICTORS.items()])
    f.legend(handles=handles)

    for i, base in enumerate(NOT_REPEATED_CORRECT_SENDS):
        print('%d/%d ' % (i + 1, len(NOT_REPEATED_CORRECT_SENDS)), end='',
            flush=True)

        a = f.add_subplot(len(NOT_REPEATED_CORRECT_SENDS), 1, i + 1)
        a.set_xlim(-WIDTH / 2, WIDTH / 2)
        a.set_ylim(0, 4)
        a.set_xticks(range(-int(WIDTH / 2), int(WIDTH / 2), int(50e3)), True)

        xs = []
        ys = []
        cs = []
        jxs = []
        jys = []
        jmys = []
        correct_send_patches = []
        predictor_patches = {predictor_name: []
                for predictor_name in PREDICTORS.keys()}
        for event in events:
            pos = event['at'] - base['at']
            if abs(pos) < WIDTH / 2:
                if 'send' in event:
                    a.axvline(pos, zorder=0, color='#d0d0d0')
                    if event['send']['fc'] == CORRECT_FC:
                        correct_send_patches.append(Rectangle((pos, 0),
                            width=event['_width'], height=4))

                    for j, (predictor_name, predictor) in enumerate(
                            PREDICTORS.items()):
                        if predictor in event.get('_predictors', []):
                            predictor_patches[predictor_name].append(
                                    Rectangle((pos, 3.75 - j / 4),
                                        width=event['_width'], height=0.25))
                elif 'recv' in event:
                    xs.append(pos)
                    ys.append(1 if event['recv']['opcode'] in {0x21, 0x23}
                            else 0.5)
                    cs.append(CNS[event['recv']['opcode']])
                    if '_delay' in event:
                        jxs.append(pos)
                        jys.append(event['_delay'] / 100e3)
                        jmys.append(((event['_delay'] + 50e3 / 2) % 50e3 -
                                50e3 / 2) / 25e3 + 2)

        a.add_collection(PatchCollection(correct_send_patches,
            facecolor='#e8f0e8'))
        for predictor_name, patches in predictor_patches.items():
            a.add_collection(PatchCollection(patches,
                facecolor=PREDICTORS[predictor_name].color))

        a.plot(jxs, jys, c='#d0d0f0', zorder=1)
        a.plot(jxs, jmys, c='#f0d0d0', zorder=1)

        a.scatter(xs, ys, 15, cs, 'o', zorder=2)

    print()

    plt.tight_layout()

    fn = 'send-wait-time-%dus_repeats-%d' % (test['send-wait-time'],
            test.get('send-repeats', 1))
    i = 0
    while True:
        ffn = os.path.join(sys.argv[2], '%s_N%03d.png' % (fn, i))
        if not os.path.exists(ffn):
            break
        i += 1
    plt.savefig(ffn)

    plt.close()
