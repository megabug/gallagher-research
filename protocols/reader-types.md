# Reader Types

These types are used in certain protocol messages to indicate reader (and implicitly, the card) types.

| Reader type ID | Name | Name in Command Centre | Data format |
|----------------|------|------------------------|-------------|
| `0x01` | 26-bit HID | HID 48 | [12B raw (manchester encoded) HID prox] |
| `0x02` | 37-bit HID | HID 96 | [24B raw (manchester encoded) HID prox] |
| `0x03` | Indala | Motorola  | `0xA0 0x00 0x00 0x00` [restB ?] |
| `0x04` | EM4100 | EM (Deister) | `0x95 0x55` [restB ?] |
| `0x05` | ? | CasiRusco | ? |
| `0x81` | ? | ? | ? | ? |
| `0x82` | ? | Unknown | ? |
| `0x83` | ? | ? | ? | ? |
| `0x84` | ? | ? | ? | ? |
| `0xF5` | (Facility code list?) | ? | ([4bit RC] [2B FC])*16 [2B CRC (little-endian)] |
| `0xF6` | ? | ? | ? | ? |
| `0xF7` | MIFARE extended data | ? | [see below](#0xF7-data-format) |
| `0xF8` | MIFARE Enhanced Security | ? | [see below](#0xF8-data-format) |
| `0xF9` | ? | "Unknown" | ? |
| `0xFA` | ? | Data Low | ? |
| `0xFB` | ? | Data High | ? |
| `0xFC` | ? | CardKey | ? |
| `0xFD` | (Used for CSN reads) | Third Party | [4/7B CSN] |
| `0xFE` | Cardax Magstripe | ? | [29B magstripe track 1] |
| `0xFF` | Cardax Prox | ? | [8B cardholder credential block] |


## `0xF8` data format

```
[16B MES block] [4/7B CSN] [2B CRC (little-endian)]
```

CRC:

* Is over *all* of a Cardax IV packet (i.e. include opcode and length: `0x03 0x19 0xF8 [data...]`) (even for GBUS!)
* Polynomial = 0x1021 (0x11021)
* Initial value = 0
* Input & result reflected


## `0xF7` data format

```
[2B subtype] [8B optional cardholder credential block]
[16B optional MES block] [4/7/10B optional CSN] [2B CRC (little-endian)]
```

Subtype:

* Bits 0-3: MIFARE card type
  - 0b00 = MIFARE Classic
  - 0b01 = MIFARE Plus (in SL3)
  - 0b10 = MIFARE DESFire

* Bit 4: ? (seen 0 for MIFARE Classic, 1 otherwise)

* Bit 5: card was proximity checked

* Bits 8-9: CSN len
  - 0b00 = 4B
  - 0b01 = 7B
  - 0b10 = 10B

* Bit 13: has cardholder credential block

* Bit 14: has MES block

* Bit 15: has CSN

CRC:

* Polynomial = 0x1021 (0x11021)
* Initial value = 0
* Input & result reflected
