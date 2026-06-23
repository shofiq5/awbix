# AWB SPACE ALLOCATION ANSWER (FFA) MESSAGE

## 1. STANDARD MESSAGE IDENTIFIER

**FFA**

## 2. MESSAGE FUNCTION

### 2.1
To reply to an AWB Space Allocation Request (FFR) Message indicating that requested space can or cannot be confirmed.

### 2.2
To reply to an AWB Space Allocation Request (FFR) Message indicating that request is being processed and that further FFA message will follow.

### 2.3
To reply to an AWB Space Allocation Request (FFR) Message confirming or refusing the accepted updates by showing the new space allocation details.

## 3. MESSAGE APPLICATION

Computer-to-Computer / Manual-to-Computer / Computer-to-Manual / Manual-to-Manual

## 4. MESSAGE EXCHANGE PARTIES

| Direction | Manual | Computer |
|-----------|--------|----------|
| **From** | The airline controlling the requested flight(s). | The access address of the cargo control computer of the airline controlling the requested flight(s). |
| **To** | The party (as indicated in the booking reference line of the FFR message) who requested space or modifications on the flight(s). | The access address of the cargo control computer (as indicated in the booking reference line of the FFR message) that requested space or modifications on the flight(s). |

## 5. MESSAGE USE

### 5.1 Multi-Airline Multi-Flight FFA Message

An airline will reply to a multi-airline multi-flight AWB Space Allocation Request (FFR) Message using an FFA message which relates only to those space allocations on flight(s) controlled by that airline.

### 5.2 Situations Where FFA Messages May Not Be Required

When cancellations (space allocation code "XX"), sale reports (space allocation codes "CA" and "SS") or background information (space allocation codes "HK" and "HL") are included in an AWB Space Allocation Request (FFR) Message and accepted as such, an FFA Message may be sent at the discretion of the message recipient.

## 6. MESSAGE EXAMPLES

### 6.1 Confirmation of AWB Space Allocation (code KK)

| Ref. | Message Content |
|------|-----------------|
| 1 | FFA/4 |
| 2 | 125-1234565FRAPHL/T12K950/BOOKS /VAL |
| 3 | BA171/19MAR/LHRJFK/KK |
| 6 | REF/FRAFCBA |

### 6.2 Rejection of AWB Space Allocation (code UU)

| Ref. | Message Content |
|------|-----------------|
| 1 | FFA/4 |
| 2 | 057-12345675BHXJFK/T5K400 |
| 3 | AF077/19MAY/CDGJFK/UU |
| 6 | REF/BHXFRBA/1234 |

### 6.3 Rejection of AWB Space Allocation because the flight does not operate (code UN)

| Ref. | Message Content |
|------|-----------------|
| 1 | FFA/4 |
| 2 | 125-12345675LHRLAX/T12K900 |
| 3 | SR3309/11JUL/ZRHLAX/UN |
| 6 | REF/LHRFWBA |

### 6.4 Wait Listing of AWB Space Allocation (code LL)

| Ref. | Message Content |
|------|-----------------|
| 1 | FFA/4 |
| 2 | 085-12345675ZRHLAX/T10K250 |
| 3 | AA123/10MAY/JFKLAX/LL |
| 6 | REF/ZRHFRSR |

### 6.5 Holding Confirmation of AWB Space Allocation (code HK)

| Ref. | Message Content |
|------|-----------------|
| 1 | FFA/4 |
| 2 | 125-21210000EDIYMX/T7K95 |
| 3 | BA073/16MAR/LHRYMX/HK |
| 6 | REF/GLAFRBA |

### 6.6 Holding Request of AWB Space Allocation (code HN)

| Ref. | Message Content |
|------|-----------------|
| 1 | FFA/4 |
| 2 | 125-21220006GLAYMX/T75K1550 |
| 3 | BA073/16MAR/LHRYMX/HN |
| 6 | REF/GLAFRBA |

### 6.7 Holding Wait Listing of AWB Space Allocation (code HL)

| Ref. | Message Content |
|------|-----------------|
| 1 | FFA/4 |
| 2 | 057-12345675JEDMIA/T3K200 |
| 3 | EA2222/10JUL/IAHMIA/HL |
| 6 | REF/PARFRAF |

### 6.8 Answer on more than one flight

| Ref. | Message Content |
|------|-----------------|
| 1 | FFA/4 |
| 2 | 160-76543213HKGYSB/T4K160 |
| 3 | AC857/19MAR/LHRYYZ/KK |
| 3 | AC363/20MAR/YYZYSB/UU |
| 6 | REF/HKGFQCX |

### 6.9 Answer with Special Service Request (SSR) and Other Service Information (OSI) on more than one line along with Shipment Reference Information

| Ref. | Message Content |
|------|-----------------|
| 1 | FFA/4 |
| 2 | 021-77777770MSPLHR/P5K5750T9 |
| 3 | AA001/19MAR/JFKLHR/KK |
| 4 | SSR/TEMP RESTRICTION OK /SPL CARE OK |
| 5 | OSI/NEED TO RCV CGO BY 1800 19MAR /AND TO MEET THE AGENT |
| 6 | REF/MSPFCNW/4923ACA |
| 7 | SRI/ABCD-12345 |

### 6.10 Acceptance of a time definite service request using the Shipment Reference Information (SRI) line

| Ref. | Message Content |
|------|-----------------|
| 1 | FFA/4 |
| 2 | 020-12345675FRAJFK/T20K800 |
| 3 | LH404/02JUN/FRAJFK/KK |
| 4 | SSR/SPECIAL SERVICE INFORMATION |
| 5 | OSI/OTHER SERVICE INFORMATION |
| 6 | REF/FRAGDLH |
| 7 | SRI/LH8520/YNZ01JUN1800/03JUN0700 |

## 7. FFA MESSAGE SPECIFICATION

### Air Waybill Space Allocation Answer
#### Cargo-IMP Manual Edition Number/Version Number

**Versions: 2-2-2-2-2-2-3-3-4-4-4-4-4-4-4** (12th through 26th edition)

### 1. Standard Message Identification

#### 1.1 Standard Message Identifier
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 101

#### 1.2 Separator : Slant
- **Status:** Mandatory

#### 1.3 Message Type Version Number
- **Status:** Mandatory
- **Character Format:** n[...3]
- **Data Element No.:** 124

#### 1.4 Separator : CRLF
- **Status:** Mandatory

### 2. Consignment Detail

#### 2.1 AWB Identification
- **Status:** Mandatory

##### 2.1.1 Airline Prefix
- **Status:** Mandatory
- **Character Format:** nnn
- **Data Element No.:** 112

##### 2.1.2 Separator : Hyphen
- **Status:** Mandatory

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
- **Note:** FFA20

##### 2.3.1 Separator : Slant
- **Status:** Mandatory

##### 2.3.2 Shipment Description Code (T or P)
- **Status:** Mandatory
- **Character Format:** a
- **Data Element No.:** 703

##### 2.3.3 Number of Pieces
- **Status:** Mandatory
- **Character Format:** n[...4]
- **Note:** FFA21
- **Data Element No.:** 701

##### 2.3.4 Weight Code
- **Status:** Mandatory
- **Character Format:** a
- **Data Element No.:** 601

##### 2.3.5 Weight
- **Status:** Mandatory
- **Character Format:** n[...7]p
- **Data Element No.:** 600

#### 2.4 Total Consignment Pieces (if 2.3.2 = P)
- **Status:** Conditional

##### 2.4.1 Shipment Description Code (T)
- **Status:** Mandatory
- **Character Format:** a
- **Data Element No.:** 703

##### 2.4.2 Number of Pieces
- **Status:** Mandatory
- **Character Format:** n[...4]
- **Data Element No.:** 701

#### 2.5 Nature of Goods
- **Status:** Optional

##### 2.5.1 Separator : Slant
- **Status:** Mandatory

##### 2.5.2 Manifest Description of Goods
- **Status:** Mandatory
- **Character Format:** t[...15]
- **Data Element No.:** 708
- **Note:** FFA34

#### 2.6 Separator : CRLF
- **Status:** Conditional
- **Note:** FFA34

#### 2.7 Special Handling Requirements
- **Status:** Optional

##### 2.7.1 Separator : Slant
- **Status:** Mandatory

##### 2.7.2 Special Handling Code
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 705

**Note:** Element 2.7 can be repeated. Can occur a maximum of nine times.

#### 2.8 Separator : CRLF
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
- **Note:** FFA22
- **Data Element No.:** 409

#### 3.6 Separator : CRLF
- **Status:** Mandatory

**Note:** Elements 3.1 thru 3.6 can be repeated.

### 4. Special Service Request
- **Status:** Optional
- **Note:** FFA23

#### 4.1 Line Identifier
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

#### 4.2 SSR Details (1st Line)
- **Status:** Mandatory

##### 4.2.1 Separator : Slant
- **Status:** Mandatory

##### 4.2.2 Special Service Request
- **Status:** Mandatory
- **Character Format:** t[...65]
- **Data Element No.:** 404

##### 4.2.3 Separator : CRLF
- **Status:** Mandatory

#### 4.3 SSR Details (2nd Line)
- **Status:** Optional

##### 4.3.1 Separator : Slant
- **Status:** Mandatory

##### 4.3.2 Special Service Request
- **Status:** Mandatory
- **Character Format:** t[...65]
- **Data Element No.:** 404

##### 4.3.3 Separator : CRLF
- **Status:** Mandatory

### 5. Other Service Information
- **Status:** Optional

#### 5.1 Line Identifier
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

#### 5.2 OSI Details (1st Line)
- **Status:** Mandatory

##### 5.2.1 Separator : Slant
- **Status:** Mandatory

##### 5.2.2 Other Service Information
- **Status:** Mandatory
- **Character Format:** t[...65]
- **Data Element No.:** 405

##### 5.2.3 Separator : CRLF
- **Status:** Mandatory

#### 5.3 OSI Details (2nd Line)
- **Status:** Optional

##### 5.3.1 Separator : Slant
- **Status:** Mandatory

##### 5.3.2 Other Service Information
- **Status:** Mandatory
- **Character Format:** t[...65]
- **Data Element No.:** 405

##### 5.3.3 Separator : CRLF
- **Status:** Mandatory

### 6. Booking Reference
- **Status:** Mandatory
- **Note:** FFA26

#### 6.1 Line Identifier
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

#### 6.2 Separator : Slant
- **Status:** Mandatory

#### 6.3 Requesting Office Message Address
- **Status:** Conditional
- **Note:** FFA25

##### 6.3.1 Airport/City Code
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 313

##### 6.3.2 Office Function Designator
- **Status:** Mandatory
- **Character Format:** mm
- **Data Element No.:** 107

##### 6.3.3 Company Designator
- **Status:** Mandatory
- **Character Format:** mm
- **Note:** GEN4
- **Data Element No.:** 308

#### 6.4 Separator : Slant
- **Status:** Conditional
- **Note:** FFA28

#### 6.5 Requesting Office File Reference
- **Status:** Optional

##### 6.5.1 Booking File Reference
- **Status:** Mandatory
- **Character Format:** t[...15]
- **Data Element No.:** 117
- **Note:** FFA27

#### 6.6 Requesting Participant Identification
- **Status:** Conditional
- **Note:** FFA27

##### 6.6.1 Separator : Slant
- **Status:** Mandatory

##### 6.6.2 Participant Identifier
- **Status:** Mandatory
- **Character Format:** m[...3]
- **Data Element No.:** 319

##### 6.6.3 Separator : Slant
- **Status:** Mandatory

##### 6.6.4 Participant Code
- **Status:** Mandatory
- **Character Format:** m[...17]
- **Data Element No.:** 320

##### 6.6.5 Separator : Slant
- **Status:** Mandatory

##### 6.6.6 Airport/City Code
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 313

#### 6.7 Separator : CRLF
- **Status:** Mandatory

### 7. Shipment Reference Information
- **Status:** Optional

#### 7.1 Line Identifier
- **Status:** Mandatory
- **Character Format:** aaa
- **Data Element No.:** 103

#### 7.2 Separator : Slant
- **Status:** Mandatory

#### 7.3 Reference Number
- **Status:** Conditional
- **Character Format:** t[...14]
- **Note:** FFA29
- **Data Element No.:** 132

#### 7.4 Separator : Slant
- **Status:** Conditional
- **Note:** FFA30

#### 7.5 Supplementary Shipment Information
- **Status:** Conditional
- **Character Format:** t[...12]
- **Note:** FFA31
- **Data Element No.:** 133

#### 7.6 Separator : Slant
- **Status:** Conditional
- **Note:** FFA32

#### 7.7 Supplementary Shipment Information
- **Status:** Conditional
- **Character Format:** t[...12]
- **Note:** FFA33
- **Data Element No.:** 133

#### 7.8 Separator : CRLF
- **Status:** Mandatory

## 8. MESSAGE NOTES

| Code | Reference | Description |
|------|-----------|-------------|
| FFA20 | Ref. 2.3 | Quantity Detail (for which space has been requested). |
| FFA21 | Ref. 2.3.3 | Number of Pieces (can be zero). |
| FFA22 | Ref. 3.5 | Space Allocation Code (see Advice Codes 1.7(b) and Status Codes 1.7(c)). |
| FFA23 | Ref. 4 | Special Service Request (reply to SSR received in FFR Message). |
| FFA25 | Ref. 6.3 | Requesting Office Message Address (to which FFA is to be sent) (if 6.6 not included). |
| FFA26 | Ref. 6 | Booking Reference (from FFR Message). |
| FFA27 | Ref. 6.6 | Requesting Participant Identification (to which FFA is to be sent) (if 6.3 not included). |
| FFA28 | Ref. 6.4 | Separator (if 6.5 and/or 6.6 included). |
| FFA29 | Ref. 7.3 | Reference Number (must be included if 7.5 and 7.7 not included but may be included with 7.5 and/or 7.7). |
| FFA30 | Ref. 7.4 | Separator (if 7.5 and/or 7.7 included). |
| FFA31 | Ref. 7.5 | Supplementary Shipment Information (must be included if 7.3 and 7.7 not included but may be included with 7.3 and/or 7.7). |
| FFA32 | Ref. 7.6 | Separator (if 7.7 included). |
| FFA33 | Ref. 7.7 | Supplementary Shipment Information (must be included if 7.3 and 7.5 not included but may be included with 7.3 and/or 7.5). |
| FFA34 | Ref. 2.6 | Separator (if 2.7 included). |

## 9. AWB SPACE ALLOCATION ANSWER MESSAGE LAYOUT

[Message layout specification end]
