# Card Application Directory

## Purpose

The Gallagher system supports having multiple site-specific credentials encoded onto a single Mifare card.

Mifare cards have the *[Mifare Application Directory](https://www.nxp.com/docs/en/application-note/AN10787.pdf)* (MAD), a NXP-defined standard for a per-card directory that allows each sector on the card to be identified. However, each sector can only be identified by a 2 byte *application ID* (Gallagher uses `0x4811` and `0x4812`). This does not allow an indication as to which sector contains which cardholder credential for a given site (region code (RC) and facility code (FC) pair).

Hence, the Gallagher-specific *Card Application Directory* (CAD) exists. This directory takes up one of the sectors on the card and allows such a mapping of (RC, FC) to sector numbers to be held. This allows readers to quickly find which sector holds the cardholder credential for a given site without the need to read each sector, avoiding delays when a user presents a card to a reader for access.

If you have access to Gallagher documentation, this is described (but the format not outlined) in the *Encoding Mifare Multiple Applications* document.


## Format

The directory is encoded onto one sector (64 bytes) as follows:

### Header

* CRC (2 bytes): This is a CRC-16 with values as follows over the next 0x2E bytes of the directory (i.e. the rest of blocks 0-2):
 - Polynomial: 0x8408 (0x18408)
 - Initial value: 0xFFFF
 - Input bytes reflected

* Unknown (1 byte): only seen to be `0x00` in the field.

* Unknown (1 byte): only seen to be `0x01` in the field.

### Mappings

Next, 12 (RC, FC) -> sector number mappings are encoded. Each is 3.5 bytes long, giving a total of 3.5 * 12 = 42 = 0x2A bytes. Each one is as follows:

* Region code (4 bits)

* Facility code (2 bytes)

* Sector number (1 byte). A sector number of 0 indicates that there are no more mappings (0 can't be a cardholder credential sector as it's reserved for the MAD).

### Padding

Lastly, the last 2 bytes are set to 0, completing blocks 0 - 2.

### Block 3

Block 3 of the sector is set in the usual Mifare-specific way, with the following settings:

* Key A: `0xA0A1A2A3A4A5` (This is the same as the MAD's key A.)

* Access rights: `0x787788`. [This indicates](https://cardinfo.barkweb.com.au/index.php?location=19&sub=20):
  - Key A: read access to data blocks and access bits
  - Key B: read access to data blocks and access bits, and write access to data blocks and keys

* User byte: `0xC1` (but `0x00` seen in the field)

* Key B: `0xB0B1B2B3B4B5` (This is the same as the MAD's key B.)


## Example

Here's an example CAD dumped from a Mifare Classic Gallagher card:

```
1B 58 00 01 C1 33 70 FD 13 38 0D 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 78 77 88 00 00 00 00 00 00 00
```

We can check the CRC (0x1B58) by calculating it over bytes 0x2 - 0x2F:

```bash
$ echo """
00 01 C1 33 70 FD 13 38 0D 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
""" | xxd -r -p | python3 -c """
import sys, crcmod
print(hex(crcmod.mkCrcFun(0x18408, 0xFFFF)(sys.stdin.buffer.read())))
"""
0x1b58
```

We can see two mappings, one with value `0xC13370F`, and another with value `0xD13380D`. These can be parsed into the following:

| RC    | FC       | Sector |
|-------|----------|--------|
| `0xC` | `0x1337` | `0x0F` |
| `0xD` | `0x1338` | `0x0D` |

Giving:

1. (RC 0xC (M), FC 0x1337 = 4919) has a cardholder credential in sector 0x0F
2. (RC 0xD (N), FC 0x1338 = 4920) has a cardholder credential in sector 0x0D.
