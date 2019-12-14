# Mifare Plus

## About

The second of the Mifare card range supported by the Gallagher system was the [Mifare Plus](https://www.nxp.com/products/rfid-nfc/mifare-hf/mifare-plus:MC_57609).

This card acts very similarly to a Mifare Classic card except for one key area: the security subsystem. The CRYPTO1-based encryption and the 6 byte keys have been replaced with 128 bit AES in a backwards-compatible way.


## Sectors

The actual data held on a Mifare Plus card is identical to that of a Mifare Classic card, so refer to [that](mifare-classic.md) documentation for more on this.


## Keys

The area that *has* changed is the keys. The fixed keys used previously have been replaced with diversified keys generated from the card's serial number (CSN) and a site-specific *Mifare Site Key*.

The algorithm used to diversify the keys is the same as that used in the Mifare DESFire cards, so refer to [that](mifare-desfire.md) documentation for the algorithm.

The inputs used for the algorithm to diversify the keys for each sector are as follows:

For the following keys, the input is simply the 2 byte key number (aka the sector the key is stored in):

* MAD key B (key numbers 0x4001 and 0x4021)
* Proximity check (key number 0xA001)
* VC polling encryption (key number 0xA080)
* VC polling MAC (key number 0xA081)

For the following keys, the input is the 4 byte CSN followed by the 2 byte key number:

* Non-MAD sector key A/B, card master (key number 0x9000)
* Card config (key number 0x9001)
* L2 switch (key number 0x9002)
* L3 switch (key number 0x9003)
* SL1 card auth (key number 0x9004)
* Select VC (key number 0xA000)

Finally, these are fixed keys:

* MAD sector A (key numbers 0x4000 and 0x4020): `0xA0A1A2A3A4A5A6A7A0A1A2A3A4A5A6A7`
