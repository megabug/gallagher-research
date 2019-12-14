# Mifare Enhanced Security

## Purpose

*Mifare Enhanced Security* (MES) was introduced by Gallagher in an attempt to strengthen the security of Mifare Classic cards. At the time, attacks had been found on the Mifare Classic card, namely the [darkside attack](https://eprint.iacr.org/2009/137) and the [hardnested attack](http://www.cs.ru.nl/~rverdult/Ciphertext-only_Cryptanalysis_on_Hardened_Mifare_Classic_Cards-CCS_2015.pdf). MES was intended to counteract these in a limited way.

The MES encodes the same data as the normal [cardholder credential](cardholder/cardholder.md), but with some additional data, and is itself encrypted with a site-specific key, the *Mifare Enhanced Security Site Key* (note that this is not the same as the *Mifare Site Key*!).

This encrypted blob of data protects against:

* Simple card cloning, where the cardholder credential sector is cloned, but the UID of the card itself (held in the meant-to-be-read-only block 0 of sector 0) is not cloned (and is different on the destination card).
* Modification of the card data, as this would require the knowledge of the MES key.

However, it does not protect against modern card cloning where the card UID *is* copied to the destination card, as the cards are then identical. Note that the MES key is not required to perform this, only if one wants to modify the data held within the MES.


## Format

The MES is an AES-encrypted 16 byte block of data.

### Data

| &nbsp; | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|--------|---|---|---|---|---|---|---|---|
| **+0** | `0x01` | CN<sub>0</sub> | CN<sub>1</sub> | CN<sub>2</sub> | FC<sub>0</sub> | FC<sub>1</sub> | RC,<br>IL | PO,<br>UX |
| **+8** |  UB,<br>UC | UD,<br>UE | CSN<sub>0</sub> | CSN<sub>1</sub> | CSN<sub>2</sub> | CSN<sub>3</sub> | R<sub>0</sub> | R<sub>1</sub> |

Note that *X<sub>Y</sub>* indicates the *Y*th byte of *X*, and *A, B* indicates the two 4 bit values *A* and *B* concatenated into a single byte (with *A* being the most significant bits and *B* the least).

Each field is named as defined in the [cardholder credential documentation](cardholder/cardholder.md), with the following additions:

* PO is the pin-offset, which is something that I Don't Understand yet, but has always been seen as 0 in the field.
* CSN is the Card Serial Number.
* R is 2 random bytes. These are obviously ignored on MES verification.

### Key

These 16 bytes are AES-encrypted with a diversified (i.e. modified per-card) key derived from the MES key and the CSN by XORing the CSN into the start of the MES key. That is, pad the CSN to 16 bytes long with 0x00s, and XOR it with the MES key.


## Example

Here is an example MES block:

```
4F 36 B7 4E FF CD 76 EF ED A5 74 58 C8 B4 E3 04
```

I know that the CSN of the card is `0x3C5451E3` and the MES site key for this card is `0x1337D00D1337D00D1337D00D1337D00D`. We can decrypt the block using the following command line:

```bash
$ echo '4F 36 B7 4E FF CD 76 EF ED A5 74 58 C8 B4 E3 04' |
xxd -r -p | openssl aes-128-ecb -d -K 2f6381ee1337d00d1337d00d1337d00d
-nopad | hd
00000000  01 00 f0 0d 13 37 c1 00  00 00 3c 54 51 e3 07 48  |.....7....<TQ..H|
00000010
```

This can be arranged:

| &nbsp; | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|--------|---|---|---|---|---|---|---|---|
| **+0** | `0x01` | CN<sub>0</sub> | CN<sub>1</sub> | CN<sub>2</sub> | FC<sub>0</sub> | FC<sub>1</sub> | RC,<br>IL | PO,<br>UX |
|        | `0x01` | `0x00` | `0xF0` | `0x0D` | `0x13` | `0x37` | `0xC1` | `0x00` |
| **+8** |  UB,<br>UC | UD,<br>UE | CSN<sub>0</sub> | CSN<sub>1</sub> | CSN<sub>2</sub> | CSN<sub>3</sub> | R<sub>0</sub> | R<sub>1</sub> |
|        | `0x00` | `0x00` | `0x3C` | `0x54` | `0x51` | `0xE3` | `0x07` | `0x48` |

This gives the following pieces of data:

* RC = 12 (M)
* FC = 0x1337 = 4919
* CN = 0xF00D = 61453
* IL = 1
* PO = 0
* CSN = 0x3C5451E3
* R = 0x0748 (which is then ignored)
* All unknown fields are 0.
