/* Dumps an Atmel chip via UART via Arduino */

#include <Arduino.h>
#include <SoftwareSerial.h>

void setup () {
	SoftwareSerial ss(4, 3);

	pinMode(2, OUTPUT);
	pinMode(5, OUTPUT);

	digitalWrite(5, LOW);

	Serial.begin(9600);
	while (!Serial);

	ss.begin(9600);

	delay(1000);

	digitalWrite(2, HIGH);
	delay(100);
	digitalWrite(2, LOW);
	delay(10);

	Serial.write("go\r\n");
	ss.write("U");
	delay(100);
	ss.write(":050000040000FFFF00F9\r\n");

	for (;;) {
		if (ss.available())
			Serial.write(ss.read());
		if (Serial.available())
			ss.write(Serial.read());
	}
}

void loop () {
}
