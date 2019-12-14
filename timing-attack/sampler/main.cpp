#include <Arduino.h>
#include <stddef.h>
#include <assert.h>

#include <TimerOne.h>

constexpr uint8_t CARDAX_PROX_MAP[] = {
	0x44, 0x04, 0x51, 0x2E, 0x4D, 0x9A, 0x84, 0xEA,
	0xF8, 0x66, 0x74, 0x29, 0x7F, 0x70, 0xD8, 0x31,
	0x7A, 0x6D, 0xA4, 0x00, 0x82, 0xB9, 0x5F, 0xB4,
	0x16, 0xAB, 0xFF, 0xC2, 0x39, 0xDC, 0x19, 0x65,
	0x57, 0x7C, 0x20, 0xFA, 0x5A, 0x49, 0x13, 0xD0,
	0xFB, 0xA8, 0x91, 0x73, 0xB1, 0x33, 0x18, 0xBE,
	0x21, 0x72, 0x48, 0xB6, 0xDB, 0xA0, 0x5D, 0xCC,
	0xE6, 0x17, 0x27, 0xE5, 0xD4, 0x53, 0x42, 0xF3,
	0xDD, 0x7B, 0x24, 0xAC, 0x2B, 0x58, 0x1E, 0xA7,
	0xE7, 0x86, 0x40, 0xD3, 0x98, 0x97, 0x71, 0xCB,
	0x3A, 0x0F, 0x01, 0x9B, 0x6E, 0x1B, 0xFC, 0x34,
	0xA6, 0xDA, 0x07, 0x0C, 0xAE, 0x37, 0xCA, 0x54,
	0xFD, 0x26, 0xFE, 0x0A, 0x45, 0xA2, 0x2A, 0xC4,
	0x12, 0x0D, 0xF5, 0x4F, 0x69, 0xE0, 0x8A, 0x77,
	0x60, 0x3F, 0x99, 0x95, 0xD2, 0x38, 0x36, 0x62,
	0xB7, 0x32, 0x7E, 0x79, 0xC0, 0x46, 0x93, 0x2F,
	0xA5, 0xBA, 0x5B, 0xAF, 0x52, 0x1D, 0xC3, 0x75,
	0xCF, 0xD6, 0x4C, 0x83, 0xE8, 0x3D, 0x30, 0x4E,
	0xBC, 0x08, 0x2D, 0x09, 0x06, 0xD9, 0x25, 0x9E,
	0x89, 0xF2, 0x96, 0x88, 0xC1, 0x8C, 0x94, 0x0B,
	0x28, 0xF0, 0x47, 0x63, 0xD5, 0xB3, 0x68, 0x56,
	0x9C, 0xF9, 0x6F, 0x41, 0x50, 0x85, 0x8B, 0x9D,
	0x59, 0xBF, 0x9F, 0xE2, 0x8E, 0x6A, 0x11, 0x23,
	0xA1, 0xCD, 0xB5, 0x7D, 0xC7, 0xA9, 0xC8, 0xEF,
	0xDF, 0x02, 0xB8, 0x03, 0x6B, 0x35, 0x3E, 0x2C,
	0x76, 0xC9, 0xDE, 0x1C, 0x4B, 0xD1, 0xED, 0x14,
	0xC5, 0xAD, 0xE9, 0x64, 0x4A, 0xEC, 0x8D, 0xF7,
	0x10, 0x43, 0x78, 0x15, 0x87, 0xE4, 0xD7, 0x92,
	0xE1, 0xEE, 0xE3, 0x90, 0xA3, 0xB0, 0x80, 0xC6,
	0xB2, 0xF4, 0x5C, 0x6C, 0x81, 0xF1, 0xBB, 0xEB,
	0x55, 0x67, 0x3C, 0x05, 0x1A, 0x0E, 0x61, 0xF6,
	0x22, 0xCE, 0xAA, 0x8F, 0xBD, 0x3B, 0x1F, 0x5E
};

constexpr auto PIN_IN = 2, PIN_OUT = 3;

constexpr auto RING_LEN = 1 << 6;

uint16_t in_buf;
auto in_bit_len = 0U;
unsigned long in_start, in_bit_start;
volatile unsigned long in_start_ring[RING_LEN];
volatile uint8_t in_opcode_ring[RING_LEN];
volatile auto in_ring_head = 0U, in_ring_tail = 0U;

template <typename T, size_t N>
constexpr size_t countof (T const (&)[N]) {
	return N;
}

constexpr unsigned long ms2us (unsigned long t) {
	return t * 1000;
}

constexpr unsigned long s2ms (unsigned long t) {
	return t * 1000;
}

uint8_t xor_bytes (const uint8_t *b, size_t len) {
	auto r = 0U;

	while (len--) {
		r ^= *(b++);
	}

	return r;
}

char hex_to_char (unsigned int i, bool upper = true) {
	if (i < 10) {
		return '0' + i;
	} else if (i < 16) {
		return (upper ? 'A' : 'a') + i - 10;
	} else {
		assert(false);
	}
}

void in_isr () {
	if (PIND & (1 << PIN_IN)) {
		in_buf <<= 1;
		if (micros() - in_bit_start >= 400) {
			in_buf |= 1;
		}
		++in_bit_len;
	} else {
		in_bit_start = micros();
		if (!in_bit_len) {
			in_start = in_bit_start;
		}
	}
}

void timer_isr () {
	if (micros() - in_bit_start < 3000) {
		return;
	}

	if (in_bit_len == 16 && ((in_buf >> 8) & 0xff) == (~in_buf & 0xff) &&
			((in_ring_head + 1) & (RING_LEN - 1))
			!= in_ring_tail) {
		in_opcode_ring[in_ring_head] = in_buf >> 8;
		in_start_ring[in_ring_head] = in_start;
		in_ring_head = (in_ring_head + 1) & (RING_LEN - 1);
	}

	in_buf = 0;
	in_bit_len = 0U;
}

bool recv_opcode (uint8_t& opcode, unsigned long& start) {
#ifdef FAKE_INPUT
	delay(random(s2ms(1)));
	opcode = random(256);
	start = micros();
	return true;
#endif

	auto r = false;

	noInterrupts();

	if (in_ring_tail != in_ring_head) {
		opcode = in_opcode_ring[in_ring_tail];
		start = in_start_ring[in_ring_tail];
		in_ring_tail = (in_ring_tail + 1) & (RING_LEN - 1);
		r = true;
	}

	interrupts();

	return r;
}

void send_bytes (const uint8_t * const bytes, size_t len,
                 unsigned long *start_time = nullptr) {
	if (start_time) {
		*start_time = micros();
	}

	for (auto i = 0U; i < len; ++i) {
		for (auto j = 0; j < 8; ++j) {
			const auto t = bytes[i] & (1 << (7 - j)) ? 168 : 47;

			PORTD |= 1 << PIN_OUT;
			delayMicroseconds(t);
			PORTD &= ~(1 << PIN_OUT);
			delayMicroseconds(231 - t);
		}
	}
}

uint8_t map_cardax_prox (uint8_t in) {
	return CARDAX_PROX_MAP[(in + 0xE4) & 0xFF];
}

void write_cardax_prox (uint8_t * const out, uint8_t region_code,
                        uint16_t facility_code, uint32_t card_number,
                        uint8_t issue_level, uint8_t unk_b = 0,
                        uint8_t unk_c = 0, uint8_t unk_d = 0,
                        uint8_t unk_e = 0) {
	assert(region_code <= 0xF);
	assert(card_number <= 0xFFFFFF);
	assert(issue_level <= 0xF);
	assert(unk_b <= 0xF);
	assert(unk_c <= 0xF);
	assert(unk_d <= 0xF);
	assert(unk_e <= 0xF);

	out[0] = map_cardax_prox(card_number >> 16);
	out[1] = map_cardax_prox(facility_code >> 4);
	out[2] = map_cardax_prox(card_number >> 3);
	out[3] = map_cardax_prox(
			((card_number & 0xF) << 5) |
			(region_code << 1) |
			(unk_b >> 4));
	out[4] = map_cardax_prox(
			((unk_b & 0xF) << 5) |
			((card_number >> 11) & 0x1F));
	out[5] = map_cardax_prox(
			(unk_e << 4) |
			(facility_code >> 12));
	out[6] = map_cardax_prox(
			(unk_c << 4) |
			unk_d);
	out[7] = map_cardax_prox(
			((facility_code & 0xF) << 4) |
			issue_level);
}

void setup () {
	Serial.begin(115200);
	while(!Serial);

	pinMode(PIN_IN, INPUT_PULLUP);
	attachInterrupt(digitalPinToInterrupt(PIN_IN), in_isr, CHANGE);
	Timer1.initialize(1500);
	Timer1.attachInterrupt(timer_isr);

	pinMode(PIN_OUT, OUTPUT);
	digitalWrite(PIN_OUT, LOW);

	randomSeed(123);

	Serial.println("ready");
}

void do_run (const unsigned long send_wait_time, const size_t send_repeats,
             const uint16_t min_fc, const uint16_t max_fc,
             const uint32_t base_cn, bool& first) {
	for (auto fc = min_fc; fc <= max_fc; ++fc) {
		for (auto i = 0U; i < send_repeats; ++i) {
			const auto cn = base_cn - i;

			uint8_t card_read[1 + 8 + 1];
			card_read[0] = 0x01;
			write_cardax_prox(&card_read[1], 0, fc, cn, 1);
			card_read[1 + 8] = xor_bytes(&card_read[1], 8);

			unsigned long send_start_time;
			send_bytes(card_read, countof(card_read),
					&send_start_time);

			if (!first) {
				Serial.println(',');
			}
			first = false;

			Serial.print("\t\t{\"at\": ");
			Serial.print(send_start_time);
			Serial.print(", \"send\": {\"fc\": ");
			Serial.print(fc);
			Serial.print(", \"cn\": ");
			Serial.print(cn);
			Serial.print("}}");

			while (micros() - send_start_time < send_wait_time) {
				uint8_t opcode;
				unsigned long recv_start_time;
				if (recv_opcode(opcode, recv_start_time)) {
					Serial.println(',');

					Serial.print("\t\t{\"at\": ");
					Serial.print(recv_start_time);
					Serial.print(", \"recv\": "
							"{\"opcode\": ");
					Serial.print(opcode);
					Serial.print("}}");
				}
			}
		}
	}
}

void loop () {
	Serial.println("[");

	const auto send_repeats = 3;

	bool first1 = true;
	for (auto send_wait_time = ms2us(200); send_wait_time <= ms2us(200);
			send_wait_time += ms2us(50)) {
		if (!first1) {
			Serial.println(',');
		}
		first1 = false;

		Serial.print("\t{\"send-wait-time\": ");
		Serial.print(send_wait_time);
		Serial.print(", \"send-repeats\": ");
		Serial.print(send_repeats);
		Serial.println(", \"runs\": [");

		delay(s2ms(10));
		uint8_t trash;
		unsigned long trash2;
		while (recv_opcode(trash, trash2));

		bool first2 = true;
		for (auto run = 0; run < 50; ++run) {
			do_run(send_wait_time, send_repeats, 50, 70,
					(1UL << 23) - 1, first2);
		}

		Serial.println();
		Serial.print("\t]}");
	}

	Serial.println();
	Serial.println("]");

	Serial.println("done");
	for (;;);
}
