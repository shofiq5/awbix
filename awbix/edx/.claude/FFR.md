# AWB SPACE ALLOCATION REQUEST (FFR) MESSAGE

## 1. STANDARD MESSAGE IDENTIFIER

**FFR**

## 2. MESSAGE FUNCTION

### 2.1
To request that space on one or more flights be allocated for a nominated consignment.

### 2.2
To request that the space allocated for a nominated consignment on one or more flights be cancelled.

### 2.3
To request that the space allocated for a nominated consignment on one or more flights be cancelled and replaced by a similar space allocation on another flight(s).

### 2.4
To add new information or to change/delete information to existing booking(s).

## 3. MESSAGE APPLICATION

Computer-to-Computer / Manual-to-Computer / Computer-to-Manual / Manual-to-Manual

## 4. MESSAGE EXCHANGE PARTIES

| Direction | Description |
|-----------|-------------|
| **From** | The party requesting space on flight(s) or updating existing booking information. |
| **To (Computer)** | The access address for the cargo control computer of the airline controlling the requested flight(s) or existing booking(s). |
| **To (Manual)** | The departure station office of the airline operating the requested flight(s) or existing booking(s). |

## 5. MESSAGE USE

### 5.1 Multi-Airline Multi-Flight FFR Message

A space allocation or an update to an existing booking may be requested for a movement requiring carriage by several airlines on several flights by:

#### 5.1.1 Single Airline FFR Message
Sending a separate "single airline" FFR message, i.e. a message listing the flight, or flights, operated by one airline on which space is requested or an existing booking updated, to each airline involved.

#### 5.1.2 Multi-Airline FFR Message
Copying the same "multi-airline" FFR message, i.e. a message listing all the flights on which space is requested or an existing booking updated, to each airline involved.

## 6. MESSAGE EXAMPLES

### 6.1 Request for AWB Space Allocation with alternative flight not acceptable (code NN)

| Ref. | Message Content |
|------|-----------------|
| 1 | FFR/8 |
| 2 | 125-12345675FRAPHL/T12K950/CLOTHING |
| 3 | BA171/19MAR/LHRJFK/NN |
| 7 | REF/FRAFCBA |

### 6.2 Request for AWB Space Allocation with alternative flight acceptable (code NA)

| Ref. | Message Content |
|------|-----------------|
| 1 | FFR/8 |
| 2 | 125-12345675FRAPHL/T10K900DG9/BOOKS /VAL |
| 3 | BA173/19MAR/LHRJFK/NA |
| 7 | REF/FRAFCBA |

### 6.3 Report of AWB Space Allocation Sale (code SS)

| Ref. | Message Content |
|------|-----------------|
| 1 | FFR/8 |
| 2 | 125-12345675HKGJFK/T3K800MC2/NEWSPAPERS |
| 3 | BA1234/25JUL/LHRJFK/SS |
| 7 | REF/HKGFRBA |

### 6.4 Cancellation of AWB Space Allocation (code XX)

| Ref. | Message Content |
|------|-----------------|
| 1 | FFR/8 |
| 2 | 125-12345675BHXMIA/P10K800T20/TV SETS |
| 3 | BA91/10JUL/BHXMIA/XX |
| 7 | REF/BHXFRBA |

### 6.5 Confirmation of AWB Space Allocation (code HK)

| Ref. | Message Content |
|------|-----------------|
| 1 | FFR/8 |
| 2 | 125-12345675MANBOM/T5K350/SPARE PARTS |
| 3 | BA1357/10JUL/LHRBOM/HK |
| 7 | REF/MANFRBA |

### 6.6 Confirmation of AWB Space Wait Listed (code HL)

| Ref. | Message Content |
|------|-----------------|
| 1 | FFR/8 |
| 2 | 057-12345675CDGANK/T8K178/CLOTHES |
| 3 | TK1221/03SEP/ISTANK/HL |
| 7 | REF/PARFRAF |

### 6.7 Requesting again AWB Space Allocation for which no answer was received (code HN)

| Ref. | Message Content |
|------|-----------------|
| 1 | FFR/8 |
| 2 | 057-12345675CDGSYD/T20K300/ENGINE PARTS |
| 3 | QF321/25AUG/MNLSYD/HN |
| 7 | REF/PARFRAF |

### 6.8 Combination of Request for AWB Space Allocation on more than one flight

| Ref. | Message Content |
|------|-----------------|
| 1 | FFR/8 |
| 2 | 057-12345675BHXJFK/T5K400/SPARE PARTS |
| 3 | AF807/18MAY/LHRCDG/NN |
| 3 | AF077/19MAY/CDGJFK/NA |
| 7 | REF/BHXFRBA/1234 |

### 6.9 Combination of Cancellation of AWB Space Allocated with a new request

| Ref. | Message Content |
|------|-----------------|
| 1 | FFR/8 |
| 2 | 125-21110003MANYMX/T4K90/ELECTRIC MOTORS |
| 3 | BA3944/18MAR/MANLHR/XX |
| 3 | BA3946/18MAR/MANLHR/NN |
| 7 | REF/LPLFRBA |

### 6.10 Request for Space Allocation with ULD Description (ULD), Special Service Request (SSR) and Other Service Information (OSI) on more than one line

| Ref. | Message Content |
|------|-----------------|
| 1 | FFR/8 |
| 2 | 021-77777770MSPLHR/P5K5750MC30.50T9/LEATH GDS /VAL/HEA |
| 3 | AA001/19MAR/JFKLHR/NN |
| 4 | ULD/5/P1G1111PAM/K1641/AVE2222NW/K705/AVE3333NW/K900 /AVA4444PA/K1004/AVM5555PA/K1500 |
| 5 | SSR/KEEP ABOVE ZERO CELSIUS /SPECIAL CARE REQUESTED DURING TRANSHIPMENT |
| 6 | OSI/MSP CONTACTS JONES NW WILSON AIR CARGO AGENTS LTD /SHIPMENT FOR OUR BEST CUSTOMER |
| 7 | REF/MSPFCNW/4923ACA |

### 6.11 Update of existing booking with overriding ULD Description (ULD), Special Service Request (SSR), Other Service Information (OSI), Dimension Information (DIM) and Shipment Reference Information (SRI)

| Ref. | Message Content |
|------|-----------------|
| 1 | FFR/8 |
| 2 | 057-12345675PARMSP/P10K3000MC10T20/ORNAMENTS /VAL/HEA |
| 3 | AF1234/10MAY/CDGORD/HK/1234 |
| 4 | ULD/1/P1P1234AF-M/K1000 |
| 5 | SSR/DO NOT DROP |
| 6 | OSI/MSP PHONE MR. SMITH AT 123-4567 |
| 7 | REF/PARFMAF/4321 |
| 8 | DIM/K1000/CMT100-200-100/2 |
| 13 | SRI/ABCD-12345 |

### 6.12 Update of existing booking with deletion of ULD Description (ULD), Special Service Request (SSR), Other Service Information (OSI), Dimension Information (DIM) and Shipment Reference Information (SRI)

| Ref. | Message Content |
|------|-----------------|
| 1 | FFR/8 |
| 2 | 057-12345675PARMSP/P10K3000MC10T20/ORNAMENTS /VAL |
| 3 | AF1234/10MAY/CDGORD/HK/1234 |
| 4 | ULD |
| 5 | SSR |
| 6 | OSI |
| 7 | REF/PARFMAF/4321 |
| 8 | DIM |
| 13 | SRI |

### 6.13 Booking request for time definite service using the Shipment Reference Information (SRI)

| Ref. | Message Content |
|------|-----------------|
| 1 | FFR/8 |
| 2 | 020-12345675FRAJFK/T20K800MC1.5/SPARE PARTS |
| 3 | LH0000/01JUN/FRAJFK/NA |
| 5 | SSR/NOTIFY IMPORT BROKER UPON ARRIVAL |
| 6 | OSI/CONTRACT RATE APPLIES |
| 7 | REF/FRAGDLH |
| 8 | DIM/K500/CMT50-50-30/10 /K300/CMT60-60-20/10 |
| 12 | CUS//2347998 /EXPRESS FORWARDING /FRANKFURT |
| 13 | SRI//QNZ01JUN0800 |

## 7. FFR MESSAGE SPECIFICATION

### Air Waybill Space Allocation Request
#### Cargo-IMP Manual Edition Number/Version Number

**Versions: 3-4-5-6-7-8** (12th to 33rd edition)

### 1. Standard Message Identification
- **Status:** Mandatory

#### 1.1 Standard Message Identifier
- **Status:** Mandatory
- **Character Format:** aaa
- **Note:** FFR1
- **Data Element No.:** 101

#### 1.2 Separator : Slant
- **Status:** Mandatory

#### 1.3 Message Type Version Number
- **Status:** Mandatory
- **Character Format:** n[...3]
- **Data Element No.:** 124

#### 1.4 Separator
- **Status:** Mandatory
- **Character Format:** CRLF

### 2. Consignment Detail
- **Status:** Mandatory
- **Note:** GEN3

#### 2.1 AWB Identification
- **Status:** Mandatory

##### 2.1.1 Airline Prefix
- **Status:** Mandatory
- **Character Format:** nnn
- **Data Element No.:** 112

##### 2.1.2 Separator
- **Status:** Mandatory
- **Character Format:** Hyphen

##### 2.1.3 AWB Serial Number
- **Status:** Mandatory
- **Character Format:** n[8]
- **Data Element No.:** 113

#### 2.2 AWB Origin and Destination
- **Status:** Mandatory

##### 2.2.1 Airport/City Code (of Origin)
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 313

##### 2.2.2 Airport/City Code (of Destination)
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 313

#### 2.3 Quantity Detail
- **Status:** Mandatory
- **Note:** FFR20

##### 2.3.1 Separator : Slant
- **Status:** Mandatory

##### 2.3.2 Shipment Description Code (T or P)
- **Status:** Mandatory
- **Character Format:** a
- **Data Element No.:** 703

##### 2.3.3 Number of Pieces
- **Status:** Mandatory
- **Character Format:** n[...4]
- **Note:** FFR21
- **Data Element No.:** 701

##### 2.3.4 Weight Code
- **Status:** Mandatory
- **Character Format:** a
- **Data Element No.:** 601

##### 2.3.5 Weight
- **Status:** Mandatory
- **Character Format:** n[...7]p
- **Data Element No.:** 600

#### 2.4 Volume Detail
- **Status:** Optional

##### 2.4.1 Volume Code
- **Status:** Optional
- **Character Format:** aa
- **Data Element No.:** 604

##### 2.4.2 Volume Amount
- **Status:** Optional
- **Character Format:** n[...9]p
- **Data Element No.:** 500

#### 2.5 Density Group
- **Status:** Optional
- **Note:** FFR22

##### 2.5.1 Density Indicator (DG)
- **Status:** Mandatory
- **Character Format:** aa
- **Data Element No.:** 603

##### 2.5.2 Density Group
- **Status:** Mandatory
- **Character Format:** n[...2]
- **Data Element No.:** 602

#### 2.6 Total Consignment Pieces (if 2.3.2 = P)
- **Status:** Conditional

##### 2.6.1 Shipment Description Code (T)
- **Status:** Mandatory
- **Character Format:** a
- **Data Element No.:** 703

##### 2.6.2 Number of Pieces
- **Status:** Mandatory
- **Character Format:** n[...4]
- **Data Element No.:** 701

#### 2.7 Nature of Goods
- **Status:** Mandatory

##### 2.7.1 Separator : Slant
- **Status:** Mandatory

##### 2.7.2 Manifest Description of Goods
- **Status:** Mandatory
- **Character Format:** t[...15]
- **Data Element No.:** 708

#### 2.8 Separator : CRLF
- **Status:** Optional
- **Note:** FFR48

#### 2.9 Special Handling Requirements
- **Status:** Optional

##### 2.9.1 Separator : Slant
- **Status:** Mandatory

##### 2.9.2 Special Handling Code
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 705

**Note:** Element 2.9 can be repeated. Can occur a maximum of nine times.

#### 2.10 Separator : CRLF
- **Status:** Mandatory

### 3. Flight Details
- **Status:** Mandatory

#### 3.1 Flight Identification
- **Status:** Mandatory

##### 3.1.1 Carrier Code
- **Status:** Mandatory
- **Character Format:** mm
- **Note:** GEN4
- **Data Element No.:** 312

##### 3.1.2 Flight Number
- **Status:** Mandatory
- **Character Format:** nnn(n)(a)
- **Data Element No.:** 800

##### 3.1.3 Separator : Slant
- **Status:** Mandatory

##### 3.1.4 Day (of Scheduled Departure)
- **Status:** Mandatory
- **Character Format:** nn
- **Note:** GEN2
- **Data Element No.:** 202

##### 3.1.5 Month (of Scheduled Departure)
- **Status:** Mandatory
- **Character Format:** aaa
- **Note:** GEN2
- **Data Element No.:** 201

#### 3.2 Separator : Slant
- **Status:** Mandatory

#### 3.3 Airports of Departure and Arrival
- **Status:** Mandatory

##### 3.3.1 Airport Code (of Departure)
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 313

##### 3.3.2 Airport Code (of Arrival)
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 313

#### 3.4 Separator : Slant
- **Status:** Mandatory

#### 3.5 Space Allocation Code
- **Status:** Mandatory
- **Character Format:** aa
- **Note:** FFR23
- **Data Element No.:** 409

#### 3.6 Allotment Identification
- **Status:** Conditional
- **Note:** FFR26

##### 3.6.1 Separator : Slant
- **Status:** Mandatory

##### 3.6.2 Allotment Identification
- **Status:** Mandatory
- **Character Format:** m[1..14]
- **Data Element No.:** 417

#### 3.7 Separator : CRLF
- **Status:** Mandatory

**Note:** Elements 3.1 thru 3.7 can be repeated.

### 4. ULD Description
- **Status:** Optional

#### 4.1 Line Identifier
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

#### 4.2 Separator : Slant
- **Status:** Mandatory

#### 4.3 Number of ULDs (Total)
- **Status:** Mandatory
- **Character Format:** n[...2]
- **Data Element No.:** 702

#### 4.4 Separator : Slant
- **Status:** Mandatory

#### 4.5 ULD Identification
- **Status:** Mandatory

##### 4.5.1 ULD Type
- **Status:** Mandatory
- **Character Format:** amm
- **Data Element No.:** 802

##### 4.5.2 ULD Serial Number
- **Status:** Optional
- **Character Format:** mnnn(n)
- **Data Element No.:** 115

##### 4.5.3 ULD Owner Code
- **Status:** Conditional
- **Character Format:** mm
- **Note:** GEN4, FFR24
- **Data Element No.:** 801

#### 4.6 ULD Position Information
- **Status:** Optional

##### 4.6.1 Separator : Hyphen
- **Status:** Mandatory

##### 4.6.2 ULD Loading Indicator
- **Status:** Mandatory
- **Character Format:** a
- **Data Element No.:** 811

#### 4.7 Weight of ULD Contents
- **Status:** Mandatory

##### 4.7.1 Separator : Slant
- **Status:** Mandatory

##### 4.7.2 Weight Code
- **Status:** Mandatory
- **Character Format:** a
- **Data Element No.:** 601

##### 4.7.3 Weight
- **Status:** Mandatory
- **Character Format:** n[...7]p
- **Data Element No.:** 600

**Note:** Elements 4.4 thru 4.7 can be repeated. Can occur a maximum of three times.

#### 4.8 Separator : CRLF
- **Status:** Mandatory

**Note:** Elements 4.4 thru 4.8 can be repeated.

### 5. Special Service Request
- **Status:** Optional

#### 5.1 Line Identifier
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

#### 5.2 SSR Details (1st Line)
- **Status:** Mandatory

##### 5.2.1 Separator : Slant
- **Status:** Mandatory

##### 5.2.2 Special Service Request
- **Status:** Mandatory
- **Character Format:** t[...65]
- **Data Element No.:** 404

##### 5.2.3 Separator : CRLF
- **Status:** Mandatory

#### 5.3 SSR Details (2nd Line)
- **Status:** Optional

##### 5.3.1 Separator : Slant
- **Status:** Mandatory

##### 5.3.2 Special Service Request
- **Status:** Mandatory
- **Character Format:** t[...65]
- **Data Element No.:** 404

##### 5.3.3 Separator : CRLF
- **Status:** Mandatory

### 6. Other Service Information
- **Status:** Optional

#### 6.1 Line Identifier
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

#### 6.2 OSI Details (1st Line)
- **Status:** Mandatory

##### 6.2.1 Separator : Slant
- **Status:** Mandatory

##### 6.2.2 Other Service Information
- **Status:** Mandatory
- **Character Format:** t[...65]
- **Data Element No.:** 405

##### 6.2.3 Separator : CRLF
- **Status:** Mandatory

#### 6.3 OSI Details (2nd Line)
- **Status:** Optional

##### 6.3.1 Separator : Slant
- **Status:** Mandatory

##### 6.3.2 Other Service Information
- **Status:** Mandatory
- **Character Format:** t[...65]
- **Data Element No.:** 405

##### 6.3.3 Separator : CRLF
- **Status:** Mandatory

### 7. Booking Reference
- **Status:** Mandatory

#### 7.1 Line Identifier
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

#### 7.2 Separator : Slant
- **Status:** Mandatory

#### 7.3 Requesting Office Message Address
- **Status:** Conditional
- **Note:** FFR25

##### 7.3.1 Airport/City Code
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 313

##### 7.3.2 Office Function Designator
- **Status:** Mandatory
- **Character Format:** mm
- **Data Element No.:** 107

##### 7.3.3 Company Designator
- **Status:** Mandatory
- **Character Format:** mm
- **Note:** GEN4
- **Data Element No.:** 308

#### 7.4 Separator : Slant
- **Status:** Conditional
- **Note:** FFR28

#### 7.5 Requesting Office File Reference
- **Status:** Optional

##### 7.5.1 Booking File Reference
- **Status:** Mandatory
- **Character Format:** t[...15]
- **Data Element No.:** 117
- **Note:** FFR27

#### 7.6 Requesting Participant Identification
- **Status:** Conditional
- **Note:** FFR27

##### 7.6.1 Separator : Slant
- **Status:** Mandatory

##### 7.6.2 Participant Identifier
- **Status:** Mandatory
- **Character Format:** m[...3]
- **Data Element No.:** 319

##### 7.6.3 Separator : Slant
- **Status:** Mandatory

##### 7.6.4 Participant Code
- **Status:** Mandatory
- **Character Format:** m[...17]
- **Data Element No.:** 320

##### 7.6.5 Separator : Slant
- **Status:** Mandatory

##### 7.6.6 Airport/City Code
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 313

#### 7.7 Separator : CRLF
- **Status:** Mandatory

### 8. Dimensions Information
- **Status:** Optional

#### 8.1 Line Identifier
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

#### 8.2 Separator : Slant
- **Status:** Mandatory

#### 8.3 Total Weight Details
- **Status:** Mandatory

##### 8.3.1 Weight Code
- **Status:** Mandatory
- **Character Format:** a
- **Data Element No.:** 601

##### 8.3.2 Weight
- **Status:** Mandatory
- **Character Format:** n[...7]p
- **Data Element No.:** 600

#### 8.4 Separator : Slant
- **Status:** Mandatory

#### 8.5 Dimensions Details
- **Status:** Mandatory

##### 8.5.1 Measurement Unit Code
- **Status:** Mandatory
- **Character Format:** m[...3]
- **Data Element No.:** 611

##### 8.5.2 Length Dimension
- **Status:** Mandatory
- **Character Format:** n[...5]
- **Data Element No.:** 608

##### 8.5.3 Separator : Hyphen
- **Status:** Mandatory

##### 8.5.4 Width Dimension
- **Status:** Mandatory
- **Character Format:** n[...5]
- **Data Element No.:** 609

##### 8.5.5 Separator : Hyphen
- **Status:** Mandatory

##### 8.5.6 Height Dimension
- **Status:** Mandatory
- **Character Format:** n[...5]
- **Data Element No.:** 610

#### 8.6 Separator : Slant
- **Status:** Mandatory

#### 8.7 Number of Pieces
- **Status:** Mandatory
- **Character Format:** n[...4]
- **Data Element No.:** 701

#### 8.8 Separator : CRLF
- **Status:** Mandatory

**Note:** Elements 8.2 thru 8.8 can be repeated.

### 9. Product Information
- **Status:** Optional

#### 9.1 Line Identifier
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

#### 9.2 Separator : Slant
- **Status:** Mandatory

#### 9.3 Service Code
- **Status:** Mandatory
- **Character Format:** a
- **Data Element No.:** 505

#### 9.4 Separator : Slant
- **Status:** Conditional
- **Note:** FFR29

#### 9.5 Rate Information
- **Status:** Optional

##### 9.5.1 Rate Class Code
- **Status:** Mandatory
- **Character Format:** a
- **Data Element No.:** 507

##### 9.5.2 Separator : Slant
- **Status:** Conditional
- **Note:** FFR30

##### 9.5.3 Commodity Item Number
- **Status:** Optional
- **Character Format:** n[4...7]
- **Note:** FFR31
- **Data Element No.:** 707

**OR**

**ULD Rate Class Type**
- **Character Format:** n(a)(a)
- **Note:** FFR32

**OR**

**Rate Class Code (Basis)**
- **Character Format:** a
- **Note:** FFR33

**Class Rate Percentage**
- **Character Format:** n[...3]

#### 9.6 Separator : CRLF
- **Status:** Mandatory

### 10. Shipper
- **Status:** Optional

#### 10.1 Line Identifier
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

#### 10.2 Account Detail
- **Status:** Optional

##### 10.2.1 Separator : Slant
- **Status:** Mandatory

##### 10.2.2 Account Number
- **Status:** Mandatory
- **Character Format:** t[...14]
- **Data Element No.:** 108

#### 10.3 Separator : CRLF
- **Status:** Mandatory

#### 10.4 Name
- **Status:** Mandatory

##### 10.4.1 Information Identifier (NAM)
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

##### 10.4.2 Separator : Slant
- **Status:** Mandatory

##### 10.4.3 Name
- **Status:** Mandatory
- **Character Format:** t[...35]
- **AWB Box:** 2
- **Data Element No.:** 300

##### 10.4.4 Separator : CRLF
- **Status:** Mandatory

**Note:** Elements 10.4.2 thru 10.4.4 can be repeated. Can occur a maximum of two times.

#### 10.5 Street Address
- **Status:** Mandatory

##### 10.5.1 Information Identifier (ADR)
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

##### 10.5.2 Separator : Slant
- **Status:** Mandatory

##### 10.5.3 Street Address
- **Status:** Mandatory
- **Character Format:** t[...35]
- **AWB Box:** 2
- **Data Element No.:** 301

##### 10.5.4 Separator : CRLF
- **Status:** Mandatory

**Note:** Elements 10.5.2 thru 10.5.4 can be repeated. Can occur a maximum of two times.

#### 10.6 Location
- **Status:** Mandatory

##### 10.6.1 Information Identifier (LOC)
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

##### 10.6.2 Separator : Slant
- **Status:** Mandatory

##### 10.6.3 Place
- **Status:** Mandatory
- **Character Format:** t[...17]
- **Note:** FFR34
- **Data Element No.:** 302

##### 10.6.4 Separator : Slant
- **Status:** Conditional
- **Note:** FFR34

##### 10.6.5 State/Province
- **Status:** Optional
- **Character Format:** t[...9]
- **Note:** FFR35
- **Data Element No.:** 303

##### 10.6.6 Separator : CRLF
- **Status:** Mandatory

#### 10.7 Coded Location
- **Status:** Mandatory
- **Note:** FFR35

##### 10.7.1 Separator : Slant
- **Status:** Mandatory

##### 10.7.2 ISO Country Code
- **Status:** Mandatory
- **Data Element No.:** 304

##### 10.7.3 Separator : Slant
- **Status:** Conditional
- **Note:** FFR36

##### 10.7.4 Post Code
- **Status:** Optional
- **Character Format:** t[...9]
- **Note:** FFR35
- **Data Element No.:** 305

#### 10.8 Contact Detail
- **Status:** Optional
- **Note:** FFR35

##### 10.8.1 Separator : Slant
- **Status:** Mandatory

##### 10.8.2 Contact Identifier
- **Status:** Mandatory
- **Character Format:** m[...3]
- **Data Element No.:** 122

##### 10.8.3 Separator : Slant
- **Status:** Mandatory

##### 10.8.4 Contact Number
- **Status:** Mandatory
- **Character Format:** m[...25]
- **Data Element No.:** 123

**Note:** Element 10.8 can be repeated.

#### 10.9 Separator : CRLF
- **Status:** Mandatory

### 11. Consignee
- **Status:** Optional

#### 11.1 Line Identifier
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

#### 11.2 Account Detail
- **Status:** Optional

##### 11.2.1 Separator : Slant
- **Status:** Mandatory

##### 11.2.2 Account Number
- **Status:** Mandatory
- **Character Format:** t[...14]
- **Data Element No.:** 108

#### 11.3 Separator : CRLF
- **Status:** Mandatory

#### 11.4 Name
- **Status:** Mandatory

##### 11.4.1 Information Identifier (NAM)
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

##### 11.4.2 Separator : Slant
- **Status:** Mandatory

##### 11.4.3 Name
- **Status:** Mandatory
- **Character Format:** t[...35]
- **AWB Box:** 2
- **Data Element No.:** 300

##### 11.4.4 Separator : CRLF
- **Status:** Mandatory

**Note:** Elements 11.4.2 thru 11.4.4 can be repeated. Can occur a maximum of two times.

#### 11.5 Street Address
- **Status:** Mandatory

##### 11.5.1 Information Identifier (ADR)
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

##### 11.5.2 Separator : Slant
- **Status:** Mandatory

##### 11.5.3 Street Address
- **Status:** Mandatory
- **Character Format:** t[...35]
- **AWB Box:** 2
- **Data Element No.:** 301

##### 11.5.4 Separator : CRLF
- **Status:** Mandatory

**Note:** Elements 11.5.2 thru 11.5.4 can be repeated. Can occur a maximum of two times.

#### 11.6 Location
- **Status:** Mandatory

##### 11.6.1 Information Identifier (LOC)
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

##### 11.6.2 Separator : Slant
- **Status:** Mandatory

##### 11.6.3 Place
- **Status:** Mandatory
- **Character Format:** t[...17]
- **Note:** FFR37
- **Data Element No.:** 302

##### 11.6.4 Separator : Slant
- **Status:** Conditional
- **Note:** FFR37

##### 11.6.5 State/Province
- **Status:** Optional
- **Character Format:** t[...9]
- **Data Element No.:** 303

##### 11.6.6 Separator : CRLF
- **Status:** Mandatory

#### 11.7 Coded Location
- **Status:** Mandatory
- **Note:** FFR38

##### 11.7.1 Separator : Slant
- **Status:** Mandatory

##### 11.7.2 ISO Country Code
- **Status:** Mandatory
- **Character Format:** aa
- **Data Element No.:** 304

##### 11.7.3 Separator : Slant
- **Status:** Conditional
- **Note:** FFR39

##### 11.7.4 Post Code
- **Status:** Optional
- **Character Format:** t[...9]
- **Note:** FFR38
- **Data Element No.:** 305

#### 11.8 Contact Detail
- **Status:** Optional
- **Note:** FFR38

##### 11.8.1 Separator : Slant
- **Status:** Mandatory

##### 11.8.2 Contact Identifier
- **Status:** Mandatory
- **Character Format:** m[...3]
- **Data Element No.:** 122

##### 11.8.3 Separator : Slant
- **Status:** Mandatory

##### 11.8.4 Contact Number
- **Status:** Mandatory
- **Character Format:** m[...25]
- **Data Element No.:** 123

**Note:** Element 11.8 can be repeated.

#### 11.9 Separator : CRLF
- **Status:** Mandatory

### 12. Customer Identification
- **Status:** Optional

#### 12.1 Line Identifier
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

#### 12.2 Account Detail
- **Status:** Optional
- **Note:** FFR40

##### 12.2.1 Separator : Slant
- **Status:** Mandatory

##### 12.2.2 Account Number
- **Status:** Optional
- **Character Format:** t[...14]
- **Data Element No.:** 108

##### 12.2.3 Separator : Slant
- **Status:** Mandatory

##### 12.2.4 IATA Cargo Agent Numeric Code
- **Status:** Optional
- **Character Format:** n[7]
- **Data Element No.:** 311

##### 12.2.5 Separator : Slant
- **Status:** Conditional
- **Note:** FFR41

##### 12.2.6 Cargo Agent CASS Address
- **Status:** Conditional
- **Character Format:** nnnn
- **Note:** FFR42
- **Data Element No.:** 309

##### 12.2.7 Separator : Slant
- **Status:** Conditional
- **Note:** FFR42

##### 12.2.8 Participant Identifier
- **Status:** Optional
- **Character Format:** m[...3]
- **Data Element No.:** 319

#### 12.3 Separator : CRLF
- **Status:** Mandatory

#### 12.4 Name
- **Status:** Mandatory

##### 12.4.1 Separator : Slant
- **Status:** Mandatory

##### 12.4.2 Name
- **Status:** Mandatory
- **Character Format:** t[...35]
- **Data Element No.:** 300

##### 12.4.3 Separator : CRLF
- **Status:** Mandatory

#### 12.5 Place
- **Status:** Mandatory

##### 12.5.1 Separator : Slant
- **Status:** Mandatory

##### 12.5.2 Place
- **Status:** Mandatory
- **Character Format:** t[...17]
- **Data Element No.:** 302

##### 12.5.3 Separator : CRLF
- **Status:** Mandatory

### 13. Shipment Reference Information
- **Status:** Optional

#### 13.1 Line Identifier
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

#### 13.2 Separator : Slant
- **Status:** Mandatory

#### 13.3 Reference Number
- **Status:** Conditional
- **Character Format:** t[...14]
- **Note:** FFR43
- **Data Element No.:** 132

#### 13.4 Separator : Slant
- **Status:** Conditional
- **Note:** FFR44

#### 13.5 Supplementary Shipment Information
- **Status:** Conditional
- **Character Format:** t[...12]
- **Note:** FFR45
- **Data Element No.:** 133

#### 13.6 Separator : Slant
- **Status:** Conditional
- **Note:** FFR46

#### 13.7 Supplementary Shipment Information
- **Status:** Conditional
- **Character Format:** t[...12]
- **Note:** FFR47
- **Data Element No.:** 133

#### 13.8 Separator : CRLF
- **Status:** Mandatory

## 8. MESSAGE NOTES

| Code | Reference | Description |
|------|-----------|-------------|
| FFR1 | Ref. 1.1 | **Updating Principles** (a) Amendments permitted are shown in FFR (b) The content of Ref. 2, 4, 5, 6, 8, 9, 10, 11, 12 and 13 shall override the existing booking information. (c) The only changes permitted to Ref. 3 — Flight Details are to Ref. 3.5 — Space Allocation Code and Ref. 3.6.2 — Allotment Identification. (d) In case of deletion of all ULD, SSR, OSI, DIM, PID, SHP, CNE, CUS and SRI information the ULD, SSR, OSI, DIM, PID, SHP, CNE, CUS and SRI lines will be limited to the line identifier only. |
| FFR20 | Ref. 2.3 | Quantity Detail (for which space has been requested). |
| FFR21 | Ref. 2.3.3 | Number of Pieces (can be zero). |
| FFR22 | Ref. 2.5 | Density Group (if no Volume Detail included). |
| FFR23 | Ref. 3.5 | Space Allocation Code (see Action Codes 1.7(a) and Status Codes 1.7(c)). Codes in 1.7(c) will reflect the latest status reached. |
| FFR24 | Ref. 4.5.3 | ULD Owner Code (if 4.5.2 included). |
| FFR25 | Ref. 7.3 | Requesting Office Message Address (to which FFA is to be sent) (if 7.6 not included). |
| FFR26 | Ref. 3.6 | Allotment Identification (if Space Allocation Code (Ref. 3.5) is "CA"). |
| FFR27 | Ref. 7.6 | Requesting Participant Identification (to which FFA is to be sent) (if 7.3 not included). |
| FFR28 | Ref. 7.4 | Separator (if 7.5 and/or 7.6 included). |
| FFR29 | Ref. 9.4 | Separator (if 9.5 included). |
| FFR30 | Ref. 9.5.2 | Separator (if 9.5.3 included). |
| FFR31 | Ref. 9.5.3 | Commodity Item Number. |
| FFR32 | Ref. 9.5.3 | ULD Rate Class Type. |
| FFR33 | Ref. 9.5.3 | Rate Class Code (Basis). |
| FFR34 | Ref. 10.6 | Separator (if 10.6.5 included). |
| FFR35 | Ref. 10.6.5 & 10.7.4 & 10.8 | State/Province, Post Code, and Contact Detail information. |
| FFR36 | Ref. 10.7.3 | Separator (if 10.7.4 included). |
| FFR37 | Ref. 11.6.4 | Separator (if 11.6.5 included). |
| FFR38 | Ref. 11.6.5 & 11.7 & 11.8 | State/Province, Coded Location, and Contact Detail information. |
| FFR39 | Ref. 11.7.3 | Separator (if 11.7.4 included). |
| FFR40 | Ref. 12.2 | Account Detail. |
| FFR41 | Ref. 12.2.5 | Separator (if 12.2.6 included). |
| FFR42 | Ref. 12.2.7 | Separator (if 12.2.8 included). |
| FFR43 | Ref. 13.3 | Reference Number (must be included if 13.5 and 13.7 not included but may be included with 13.5 and/or 13.7). |
| FFR44 | Ref. 13.4 | Separator (if 13.5 and/or 13.7 included). |
| FFR45 | Ref. 13.5 | Supplementary Shipment Information (must be included if 13.3 and 13.7 not included but may be included with 13.3 and/or 13.7). |
| FFR46 | Ref. 13.6 | Separator (if 13.7 included). |
| FFR47 | Ref. 13.7 | Supplementary Shipment Information (must be included if 13.3 and 13.5 not included but may be included with 13.3 and/or 13.5). |
| FFR48 | Ref. 2.8 | Separator (if 2.9 included). |
