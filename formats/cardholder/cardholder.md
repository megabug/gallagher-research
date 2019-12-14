# Cardholder Credential Format

## Data

The key piece of data used to represent a cardholder in a Gallagher system is a "cardholder credential". This consists of a tuple of items:

* A 4-bit *region code* (RC). Usually displayed as a letter from `A`-`P`.
* A 16-bit *facility code* (FC). Usually displayed alongside the region code (e.g. `A12345`).
* A 24-bit *card number* (CN). These nominally start from 1 and are usually seen in the field to range up to ~50,000.
* A 4-bit *issue level* (IL). These are intended to start at 1 and be incremented each time the credential needs to be re-issued (e.g. due to a card being lost or stolen).

The region and facility codes pair represents a unique site installation, while the card number and issue level pair represents a unique physical card.

There are also some unknown data items referred to in firmware which have only ever been seen set to 0 in the field, here labeled UB, UC, UD, UE and UX (for historical research reasons). It appears to be safe to always set these to 0.


## Encoding

This tuple of data is not encoded directly onto cards but is instead obfuscated into an 8 byte format.

First, the items (but not UX) are arranged into 8 bytes as follows:

| &nbsp;     | Bit 7           | Bit 6           | Bit 5           | Bit 4           | Bit 3           | Bit 2           | Bit 1           | Bit 0           |
|------------|-----------------|-----------------|-----------------|-----------------|-----------------|-----------------|-----------------|-----------------|
| **Byte 0** | CN<sub>23</sub> | CN<sub>22</sub> | CN<sub>21</sub> | CN<sub>20</sub> | CN<sub>19</sub> | CN<sub>18</sub> | CN<sub>17</sub> | CN<sub>16</sub> |
| **Byte 1** | FC<sub>11</sub> | FC<sub>10</sub> | FC<sub>9</sub>  | FC<sub>8</sub>  | FC<sub>7</sub>  | FC<sub>6</sub>  | FC<sub>5</sub>  | FC<sub>4</sub>  |
| **Byte 2** | CN<sub>10</sub> | CN<sub>9</sub>  | CN<sub>8</sub>  | CN<sub>7</sub>  | CN<sub>6</sub>  | CN<sub>5</sub>  | CN<sub>4</sub>  | CN<sub>3</sub>  |
| **Byte 3** | CN<sub>2</sub>  | CN<sub>1</sub>  | CN<sub>0</sub>  | RC<sub>3</sub>  | RC<sub>2</sub>  | RC<sub>1</sub>  | RC<sub>0</sub>  | UB<sub>3</sub>  |
| **Byte 4** | UB<sub>2</sub>  | UB<sub>1</sub>  | UB<sub>0</sub>  | CN<sub>15</sub> | CN<sub>14</sub> | CN<sub>13</sub> | CN<sub>12</sub> | CN<sub>11</sub> |
| **Byte 5** | UE<sub>3</sub>  | UE<sub>2</sub>  | UE<sub>1</sub>  | UE<sub>0</sub>  | FC<sub>15</sub> | FC<sub>14</sub> | FC<sub>13</sub> | FC<sub>12</sub> |
| **Byte 6** | UC<sub>3</sub>  | UC<sub>2</sub>  | UC<sub>1</sub>  | UC<sub>0</sub>  | UD<sub>3</sub>  | UD<sub>2</sub>  | UD<sub>1</sub>  | UD<sub>0</sub>  |
| **Byte 7** | FC<sub>3</sub>  | FC<sub>2</sub>  | FC<sub>1</sub>  | FC<sub>0</sub>  | IL<sub>3</sub>  | IL<sub>2</sub>  | IL<sub>1</sub>  | IL<sub>0</sub>  |

(Here, *X<sub>Y</sub>* represents the *Y*th bit of *X*, where the 0th is the least significant bit.)

Then, the 8 resultant bytes are mapped through a substitution table (aka an [S-box](https://en.wikipedia.org/wiki/S-box)) to produce the final 8 byte output:

| &nbsp; | 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 0A | 0B | 0C | 0D | 0E | 0F |
|--------|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|
| **00** | A3 | B0 | 80 | C6 | B2 | F4 | 5C | 6C | 81 | F1 | BB | EB | 55 | 67 | 3C | 05 |
| **10** | 1A | 0E | 61 | F6 | 22 | CE | AA | 8F | BD | 3B | 1F | 5E | 44 | 04 | 51 | 2E |
| **20** | 4D | 9A | 84 | EA | F8 | 66 | 74 | 29 | 7F | 70 | D8 | 31 | 7A | 6D | A4 | 00 |
| **30** | 82 | B9 | 5F | B4 | 16 | AB | FF | C2 | 39 | DC | 19 | 65 | 57 | 7C | 20 | FA |
| **40** | 5A | 49 | 13 | D0 | FB | A8 | 91 | 73 | B1 | 33 | 18 | BE | 21 | 72 | 48 | B6 |
| **50** | DB | A0 | 5D | CC | E6 | 17 | 27 | E5 | D4 | 53 | 42 | F3 | DD | 7B | 24 | AC |
| **60** | 2B | 58 | 1E | A7 | E7 | 86 | 40 | D3 | 98 | 97 | 71 | CB | 3A | 0F | 01 | 9B |
| **70** | 6E | 1B | FC | 34 | A6 | DA | 07 | 0C | AE | 37 | CA | 54 | FD | 26 | FE | 0A |
| **80** | 45 | A2 | 2A | C4 | 12 | 0D | F5 | 4F | 69 | E0 | 8A | 77 | 60 | 3F | 99 | 95 |
| **90** | D2 | 38 | 36 | 62 | B7 | 32 | 7E | 79 | C0 | 46 | 93 | 2F | A5 | BA | 5B | AF |
| **A0** | 52 | 1D | C3 | 75 | CF | D6 | 4C | 83 | E8 | 3D | 30 | 4E | BC | 08 | 2D | 09 |
| **B0** | 06 | D9 | 25 | 9E | 89 | F2 | 96 | 88 | C1 | 8C | 94 | 0B | 28 | F0 | 47 | 63 |
| **C0** | D5 | B3 | 68 | 56 | 9C | F9 | 6F | 41 | 50 | 85 | 8B | 9D | 59 | BF | 9F | E2 |
| **D0** | 8E | 6A | 11 | 23 | A1 | CD | B5 | 7D | C7 | A9 | C8 | EF | DF | 02 | B8 | 03 |
| **E0** | 6B | 35 | 3E | 2C | 76 | C9 | DE | 1C | 4B | D1 | ED | 14 | C5 | AD | E9 | 64 |
| **F0** | 4A | EC | 8D | F7 | 10 | 43 | 78 | 15 | 87 | E4 | D7 | 92 | E1 | EE | E3 | 90 |

(The raw 256 byte subtitution table is available [here](substitution-table.bin)).

These 8 bytes are then stored on the card using the required [card-specific format](../card-specific).


## Example

### Encoding

Take the cardholder credential (RC 0 (A), FC 9876, CN 1234, IL 1).

First, arrange the data into 8 bytes as follows:

| &nbsp;     | Bit 7 | Bit 6 | Bit 5 | Bit 4 | Bit 3 | Bit 2 | Bit 1 | Bit 0 |
|------------|-------|-------|-------|-------|-------|-------|-------|-------|
| **Byte 0** | 0     | 0     | 0     | 0     | 0     | 0     | 0     | 0     |
| **Byte 1** | 0     | 1     | 1     | 0     | 1     | 0     | 0     | 1     |
| **Byte 2** | 1     | 0     | 0     | 1     | 1     | 0     | 1     | 0     |
| **Byte 3** | 0     | 1     | 0     | 0     | 0     | 0     | 0     | 0     |
| **Byte 4** | 0     | 0     | 0     | 0     | 0     | 0     | 0     | 0     |
| **Byte 5** | 0     | 0     | 0     | 0     | 0     | 0     | 1     | 0     |
| **Byte 6** | 0     | 0     | 0     | 0     | 0     | 0     | 0     | 0     |
| **Byte 7** | 0     | 1     | 0     | 0     | 0     | 0     | 0     | 1     |

This gives the 8 byte value `0x00699A4000020041`. Next, map each byte through the substitution table:

`00` -> `A3`

`69` -> `97`

`9A` -> `93`

`40` -> `5A`

`00` -> `A3`

`02` -> `80`

`00` -> `A3`

`41` -> `49`

This gives the final result, `0xA397935AA380AA49`.

### Decoding

Take `0xA38A8A4BA3A3A32C` as input. First, map each byte through the inverted subsitution table:

`A3` -> `00`

`8A` -> `8A`

`8A` -> `8A`

`4B` -> `E8`

`A3` -> `00`

`A3` -> `00`

`A3` -> `00`

`2C` -> `E3`

This gives `0x008A8AE8000000E3`. Next, arrange the data and read out the constituent parts:

| &nbsp;     | Bit 7 | Bit 6 | Bit 5 | Bit 4 | Bit 3 | Bit 2 | Bit 1 | Bit 0 |
|------------|-------|-------|-------|-------|-------|-------|-------|-------|
| **Byte 0** | 0     | 0     | 0     | 0     | 0     | 0     | 0     | 0     |
| **Byte 1** | 1     | 0     | 0     | 0     | 1     | 0     | 1     | 0     |
| **Byte 2** | 1     | 0     | 0     | 0     | 1     | 0     | 1     | 0     |
| **Byte 3** | 1     | 1     | 1     | 0     | 1     | 0     | 0     | 0     |
| **Byte 4** | 0     | 0     | 0     | 0     | 0     | 0     | 0     | 0     |
| **Byte 5** | 0     | 0     | 0     | 0     | 0     | 0     | 0     | 0     |
| **Byte 6** | 0     | 0     | 0     | 0     | 0     | 0     | 0     | 0     |
| **Byte 7** | 1     | 1     | 1     | 0     | 0     | 0     | 1     | 1     |

This gives a resulting credential of (RC 4 (D), FC 2222, CN 1111, IN 3) (and all unknown fields set to 0).
