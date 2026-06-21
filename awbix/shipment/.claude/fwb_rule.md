# AIR WAYBILL DATA (FWB) MESSAGE

## 1. STANDARD MESSAGE IDENTIFIER

**FWB**

## 2. MESSAGE FUNCTION

To transmit a complete set of Air Waybill data in accordance with the Cargo Services Conference Resolutions Manual.

## 3. MESSAGE APPLICATION

Computer-to-Computer.

## 4. MESSAGE EXCHANGE PARTIES

- **From:** the access address of the Cargo Control Computer of a participant involved in the movement of a consignment.
- **To (Computer):** the access address of the Cargo Control Computer of a participant involved in the movement of a consignment.
- **To (Manual):** the message address of the requestor for Air Waybill data as indicated in the last line of the FWR message.

## 5. MESSAGE USE

### 5.1 Intention

To eliminate the need to re-enter Air Waybill data which has been already entered by an earlier participant in the movement of a consignment. To eliminate the need for the paper copy of an air waybill to accompany the consignment in accordance with ICAO Annex 9, Section B, Chapter 4.

### 5.2 Various cases where a FWB message is used

- When a cargo agent delivers a consignment to an airline
- When an airline transfers a consignment to another airline
- When an airline delivers a consignment to a handling party
- When a handling party delivers a consignment to an airline
- When an airline delivers a consignment to a cargo agent
- When a participant requests Air Waybill data by a FWR message

### 5.3 When to send an automatic FWB message

- An unsolicited FWB message must be sent prior to the physical delivery of the goods

## 6. MESSAGE EXAMPLES

### 6.1 Agent to Airline Message

Indicating:
- A minimum charge
- A declared value for customs (see Attachment 2)

**Message Content Example:**
```
1 FWB/17
2 777-12345675BOMSUV/T1K3.5
4 RTG/SUVII
5 SHP
  NAM/T. ULSIDAS LTD.
  ADR/105 VEER TAMAN ROAD
  LOC/MUMBAI
  /IN
6 CNE
  NAM/J. JONES IMPORTERS
  ADR/.
  LOC/SUVA
  /FJ
7 AGT//1430288
  /SPEEDAIR SERVICES
  /MUMBAI
11 CVD/INR//PP/NVD/1500.00/XXX
12 RTD/1/P1/K3.5/CM/W3.5/R800.00/T800.00
  /NG/CLOTH SAMPLES
  /2/ND//NDA
14 PPD/WT800.00
  /CT800.00
16 CER/T.ULSIDAS LTD.
17 ISU/01OCT06/MUMBAI/SPEEDAIR SERVICES
20 REF///AGT/SPEEDAIRSERVICES/BOM
```

### 6.2 Airline to Airline Message

Indicating:
- A class rate based on the normal rate (for live animals)
- A charge for an animal container
- Volume (not shown on AWB example but calculated according dimensions)

### 6.3 Airline to Cargo Community System Message

Indicating a consignment of dangerous goods, acceptable for carriage on a passenger aircraft, and mixed with non-dangerous goods.

### 6.4 Forwarder to Airline Message

Indicating:
- A consolidated consignment, presented on one skid
- An indication that the agent reports the house waybill details directly to Customs
- An indication that a local transfer at destination is required
- Application of a Shippers Load and Count (SLAC)
- An indication that the consolidation is secure

## 7. FWB MESSAGE SPECIFICATION

### 1. Standard Message Identification

#### 1.1 Standard Message Identifier
- **Status:** GEN1
- **Character Format:** aaa
- **Data Element No.:** 101

#### 1.2 Separator: Slant

#### 1.3 Message Type Version Number
- **Character Format:** n[...3]
- **Data Element No.:** 124

#### 1.4 Separator: CRLF

### 2. AWB Consignment Details

#### 2.1 AWB Identification

**2.1.1 Airline Prefix**
- **Character Format:** nnn
- **AWB Box:** 1A
- **Data Element No.:** 112

**2.1.2 Separator:** Hyphen
- **AWB Box:** 1B
- **Data Element No.:** 113

**2.1.3 AWB Serial Number**
- **Character Format:** n[8]
- **Data Element No.:** 313

#### 2.2 AWB Origin and Destination

**2.2.1 Airport/City Code (of Origin)**
- **Character Format:** aaa
- **AWB Box:** 1, 9

**2.2.2 Airport/City Code (of Destination)**
- **Character Format:** aaa
- **AWB Box:** 18

#### 2.3 Quantity Detail

**2.3.1 Separator:** Slant

**2.3.2 Shipment Description Code (T)**
- **Character Format:** a
- **Data Element No.:** 703

**2.3.3 Number of Pieces**
- **Character Format:** n[...4]
- **Note:** FWB66
- **AWB Box:** 22J
- **Data Element No.:** 701

**2.3.4 Weight Code**
- **Character Format:** a
- **AWB Box:** 22C
- **Data Element No.:** 601

**2.3.5 Weight**
- **Character Format:** n[...7]p
- **Note:** FWB67
- **AWB Box:** 22K
- **Data Element No.:** 600

#### 2.4 Volume Detail

**2.4.1 Volume Code**
- **Character Format:** aa
- **Data Element No.:** 604

**2.4.2 Volume Amount**
- **Character Format:** n[...9]p
- **Data Element No.:** 500

#### 2.5 Density Group

**2.5.1 Density Indicator (DG)**
- **Character Format:** aa
- **Data Element No.:** 603

**2.5.2 Density Group**
- **Character Format:** n[...2]
- **Data Element No.:** 602

#### 2.6 Separator: CRLF

## Notes

This document contains detailed specifications for the FWB (Air Waybill Data) message format as per IATA standards. It includes comprehensive section definitions for all message components including flight bookings, routing, shipper details, charges, and customs information.

Refer to individual FWB notes (FWB1-FWB85) for additional context and conditional requirements for message elements.
