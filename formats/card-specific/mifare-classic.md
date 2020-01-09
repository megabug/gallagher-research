# MIFARE Classic

## About

The first of the MIFARE card range supported by the Gallagher system was the [MIFARE Classic](https://www.nxp.com/products/rfid-nfc/mifare-hf/mifare-classic:MC_41863).


## Sectors

The cards will have a valid [MIFARE Application Directory](https://www.nxp.com/docs/en/application-note/AN10787.pdf). The following application IDs are used by the Gallagher system:

* `0x4811`: [Card Application Directory](../cad.md) (CAD) sector
* `0x4812`: Site-specific card data sector (see below).

There will be at least one cardholder credential data sector; usually this is sector 15.

If there is a CAD sector, it will usually be in sector 14.

Finally, there may be additional cardholder credential data sectors; usually these start at sector 13 and move downward.


## Site-specific Card Data Sector

This sector holds a cardholder information for a specific site. The format is as follows:

### Block 0

Contains an 8 byte [cardholder credential data](../cardholder/cardholder.md) block, followed by its bitwise inverse.

### Block 1

Contains the literal string <tt>www&#x2e;cardax.com&nbsp;&nbsp;</tt> (note the 2 padding spaces).

### Block 2

If enabled for the site, contains a 16 byte [MIFARE Enhanced Security](../mes.md) block. Otherwise, should contain all zeroes. However, cards have been seen in the field that appear to contain uninitialised data from the stack during the encoding process!

### Block 3

Block 3 is set in the usual MIFARE-specific way, with the following settings:

* Key A: `0x160A91D29A9C`

* Access rights: `0x787788`. [This indicates](https://cardinfo.barkweb.com.au/index.php?location=19&sub=20):
  - Key A: read access to data blocks and access bits
  - Key B: read access to data blocks and access bits, and write access to data blocks and keys

* User byte: `0x1D` if MES present, else `0xC1`

* Key B: `0xB7BF0C13066E`


## Example

Here's an example MIFARE Classic card, sector-by-sector.

First, sector 0 contains the MAD:

```
E3 51 54 3C DA 08 04 00 01 6F 01 6D 45 68 F8 1D
BD 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 12 48 11 48 12 48
00 00 00 00 00 00 78 77 88 C1 00 00 00 00 00 00
```

As we can see, sector 14 holds a CAD (AID `0x4811`) and sectors 13 and 15 site-specific data (AID `0x4812`).

Looking at sector 14, we can see the CAD:

```
1B 58 00 01 C1 33 70 FD 13 38 0D 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 78 77 88 00 00 00 00 00 00 00
```

[Decoding the CAD](../cad.md#example), we see the following information:

| RC    | FC       | Sector |
|-------|----------|--------|
| `0xC` | `0x1337` | `0x0F` |
| `0xD` | `0x1338` | `0x0D` |

Sector 15 gives the actual credential data:

```
A3 B4 B0 C1 51 B0 A3 1B 5C 4B 4F 3E AE 4F 5C E4
77 77 77 2E 63 61 72 64 61 78 2E 63 6F 6D 20 20
4B C7 41 C0 E3 A7 63 B6 F1 29 84 8C 56 44 AC B0
00 00 00 00 00 00 78 77 88 1D 00 00 00 00 00 00
```

Here we see the card credential data of `0xA3B4B0C151B0A31B` and a MES block of `0x4BC741C0E3A763B6F129848C5644ACB0`.

The card credential data [decodes](../cardholder/cardholder.md) to (RC 12 (M), FC 0x1337 = 4919, CN 0xF00D = 61453, IL 1).
