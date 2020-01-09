## About

This repository is a collection of notes and source code produced as part of research on the Gallagher (aka Cardax) access control system. It is intended for use by other security researchers, but may prove useful to system operators and installers as well.

Each area of research (such as a protocol or format) is described in a separate directory. For an overview of the totality of the research, please see below.

You can help! If you see errors or omissions in the notes or encounter problems with the code please send an issue and/or pull request :)


## Talk

This research was presented as talk at [Kawaiicon](https://kawaiicon.org/), a New Zealand information security conference. **You can view the talk and see the slides [here](https://www.youtube.com/watch?v=brhXqyidiKo).**


## Overview for attackers

This overview assumes that you are an unauthorised person wanting to gain access to a Gallagher-secured site (i.e. as part of a legal physical security audit). There is a well-defined process that must be undertaken, outlined here:

### 1. Get card credential data

The key piece of data used as an authentication credential in the Gallagher system is what is defined here as "card credential data". This consists of a tuple of 4 items:

* A 4-bit *region code* (RC), usually displayed as a letter from A-P.
* A 16-bit *facility code* (FC), usually displayed alongside the region code (e.g. `A12345`).
* A 24-bit *card number* (CN). These nominally start from 1 and are usually seen in the field to range up to ~50,000.
* A 4-bit *issue level* (IL). These are intended to start at 1.

The region and facility codes are intended to represent a unique site installation, while the card number and issue level represent a single card credential. The issue level starts at 1 for any given card credential and is intended to be incremented each time the credential needs to be re-issued (e.g. due to a card being lost or stolen).

There are several ways to gain access to this data, but these usually either target a site's cards or readers.

#### Targeting site cards

The obvious solution is to attempt to read these credentials off an existing valid card. This repository has the [formats](formats/) for each kind of supported card in the Gallagher system. To gain access to the data in the first place, one of three forms of attacks can be performed:

##### Reading a card directly

If you have access to a valid credential, it is a simple matter of reading the card using a tool such as a Proxmark3 (not gonna try and link one of the many variants) to dump the required encoding/sectors/files off the card. As not all kinds of cards are fully supported for reading, it may be necessary to manually send commands (APDUs) to some kinds of card to read them.

##### Reading a card from a distance (skimming)

It is well-known that it is possible to read both low-freqency and high-frequency RFID cards from some distance. Possible tools to do so include a Proxmark3 or a software-defined radio (SDR) with a suitable antenna.

##### Observing a card-reader transaction from a distance (interception)

The limitation in performing the previously-described skimming attack is on powering the card from a distance. The power required to energise the card increases with distance, making it almost impossible at reasonable distances, especially for high-frequency cards.

The alternative is to intercept a transaction between a card and a legitimate reader. While the reader powers the card only a short distance, the actually communications between the card and reader can be seen from a much longer distance, allowing this attack to be more useful in the field. To do so, a software-defined radio (SDR) with a suitable long-range antenna and software to transcieve signals was the approach taken as part of this research and is outlined [here](sdr/sdr.md).

#### Targeting site controllers

Less obvious is the ability to ascertain the required card credential information from legitmate controllers themselves. Readers are connected (eventually) to controllers, meaning that if one has physical access to a reader, there is also access to the controller via the reader-controller connection. The protocols used in these connections are outlined [here](protocols/). With knowledge of these protocols it is possible to perform a brute-force attack upon the controller. With hints leaked via a timing-based side channel, it is possible to narrow down the otherwise large search space and find valid facility codes and card numbers in a feasible amount of time. This approach is outlined [here](timing-attack/timing-attack.md).

### 2. Decode, modify, and re-encode card data (optional)

The card credential data obtained in step 1 will not be the raw tuple given earlier, but instead an obfuscated block of data. While not necessary, it may be desired to decode this data into the raw tuple so that it is possible to modify the individual credential elements. For example, once one card credential is gained, it is possible to decode it, modify the card number, and re-encode it. This allows the capture of one card's data to lead to compromise of all cards for that site, potentially allowing an escalation of privilege.

The encoded format of the card credential data is given [here](formats/cardholder/cardholder.md) alongside [scripts](formats/cardholder/) for decoding and encoding the data to and from its constituent parts.

### 3. Send card credential data

The last step is to make use of captured (and potentially modified) data. To do so, one can encode the data to a new physical RFID card, or simply replay it (aka. emulate it) to a reader.

#### Encoding

It is possible to use devices such as a Proxmark3 to encode several formats of RFID card. Since the support is not as extensive as it is for reading, it may be necessary to again manually send commands (APDUs) to some kinds of card to encode them.

#### Replaying (emulation)

The same devices usually support replaying the card data over the air to a reader which cuts down on the effort required.


## Overview for defenders

This overview assumes that you are an authorised person wanting to secure access to a Gallagher-secured site (i.e. as part of a facility security team).

The attacks given in this research mainly come down to the use of weak RFID card formats and settings. As outlined by Gallagher, the only form of Mifare-based credential that is currently considered secure against attack is the Mifare DESFire or Mifare Plus card **with** a non-default Mifare site key. (There are non-Mifare credentials that are also considered secure, such as PIV or FIDO-based ones).

If other forms of card (i.e. Cardax LF or Mifare Classic) are in use, it is trivial to bypass the protection (if any) the card attempts to mount against an illegitate reader from reading the card credential data.

If a Mifare DESFire or Mifare Plus card is in use on a site *but* the default Mifare site key is used, then it is still possible, with knowledge of this default site key, to read card credential data from the cards.

Gallagher provides resources to system operators and installers looking to secure their system:

* Hardening guides, namely the *Gallagher Command Centre Hardening Guide* and the *Gallagher Controller 6000 Hardening Guide*, provided as part of the documentation of a Command Centre installation.
* The *[Gallagher Security Health Check](https://security.gallagher.com/products/security-health-check)*. This first-of-its-kind tool allows information to be gathered on the security posture of a site, where it can then be sent to Gallagher for analysis and transformation into a [report](https://security.gallagher.com/media/2129/shc-sample-report.pdf). All of the recommendations made above are checked by this tool, and I highly recommend its use.


## Future directions

While the information found so far is definitely useful in the field, there are more technologies and subsystems to look at! Eventually, I would like to additionally look at:

* The HBUS protocol in more depth (i.e. beyond the authentication phase)
* Bluetooth credentials
* PIV credentials (unlikely though - requires specialised hardware)


## Licensing

All source code in this repository is [MIT licensed](LICENSE).
