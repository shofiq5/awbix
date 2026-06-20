# FSU Message 14 Data Elements

**Message Type**: FSU (Functional Status Update)  
**Message Version**: 14  
**Standard Code**: CargoIMP  
**Default Message**: Yes

---

## Standard Message Identification

| Ref Num | Condition | Message Data Element Name | Data Format | Data Element Code | Check Ind | Fixed Value | Sort Seq |
|---------|-----------|--------------------------|-------------|-------------------|-----------|-------------|---------|
| 1 | M | Standard Message Identification | - | - | - | - | 1 |
| 1.1 | M | Standard Message Identifier | aaa | 101 | - | FSU | 2 |
| 1.2 | M | Separator | Slant | - | - | - | 3 |
| 1.3 | M | Message Type Version Number | n[...3] | 124 | - | - | 4 |
| 1.4 | M | Separator | CRLF | - | - | - | 5 |

---

## Consignment Detail (Section 2)

| Ref Num | Condition | Message Data Element Name | Data Format | Data Element Code | Check Ind | Fixed Value | Sort Seq |
|---------|-----------|--------------------------|-------------|-------------------|-----------|-------------|---------|
| 2 | M | Consignment Detail | - | - | - | - | 6 |
| 2.1 | M | AWB Identification | - | - | - | - | 7 |
| 2.1.1 | M | Airline Prefix | nnn | 112 | - | - | 8 |
| 2.1.2 | M | Separator | Hyphen | - | - | - | 9 |
| 2.1.3 | M | AWB Serial Number | n[8] | 113 | - | - | 10 |
| 2.2 | O | AWB Origin and Destination | - | - | - | - | 11 |
| 2.2.1 | M | AWB Origin | aaa | 313 | - | - | 12 |
| 2.2.2 | M | AWB Destination | aaa | 313 | - | - | 13 |
| 2.3 | O | Consignment Quantity Detail | - | - | - | - | 14 |
| 2.3.1 | M | Separator | Slant | - | - | - | 15 |
| 2.3.2 | M | Shipment Desc Code | a | 703 | Y | - | 16 |
| 2.3.3 | M | Number of Pieces | n[...4] | - | - | - | 17 |
| 2.3.4 | O | Weight Code | a | 601 | Y | - | 18 |
| 2.3.5 | O | Weight | n[...7]p | 600 | - | - | 19 |
| 2.4 | O | Total Consignment Pieces | - | - | - | - | 20 |
| 2.4.1 | M | Shipment Description Code | a | 703 | - | T | 21 |
| 2.4.2 | M | Number of Pieces | n[...4] | 701 | - | - | 22 |
| 2.5 | M | Separator | CRLF | - | - | - | 23 |

---

## Status Details - RCS (Received Consignment at Sorting)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 3 | O | Status Details RCS | - | - | - | 24 |
| 3.1 | M | Status Code RCS | aaa | 400 | RCS | 25 |
| 3.3.1 | M | Day of Receipt | nn | 202 | - | 28 |
| 3.3.2 | M | Month of Receipt | aaa | 201 | - | 29 |
| 3.3.3 | O | Actual Time | nnnn | 203 | - | 30 |
| 3.3.5 | M | Airport Code of Receipt | aaa | 313 | - | 32 |

---

## Status Details - RCT (Received Consignment by Transfer)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 4 | O | Status Details RCT | - | - | - | 52 |
| 4.1 | M | Status Code RCT | aaa | 400 | RCT | 53 |
| 4.3.1 | M | Carrier Code | mm | 312 | - | 56 |
| 4.3.3 | M | Day of Transfer | nn | 202 | - | 58 |
| 4.3.4 | M | Month of Transfer | aaa | 201 | - | 59 |

---

## Status Details - RCF (Ready for Carriage Flight)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 5 | O | Status Details RCF | - | - | - | 76 |
| 5.1 | M | Status Code RCF | aaa | 400 | RCF | 77 |
| 5.3.1 | O | Carrier Code | mm | 312 | - | 80 |
| 5.3.2 | O | Flight Number | nnn(n)(a) | 800 | - | 81 |
| 5.3.4 | M | Day of Scheduled Arrival | nn | 202 | - | 83 |
| 5.3.5 | M | Month of Scheduled Arrival | aaa | 201 | - | 84 |
| 5.3.10 | M | Airport Code of Arrival | aaa | 313 | - | 89 |

---

## Status Details - BKD (Booking)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 6 | O | Status Details BKD | - | - | - | 109 |
| 6.1 | M | Status Code BKD | aaa | 400 | BKD | 110 |
| 6.3.1 | O | Carrier Code | mm | 312 | - | 113 |
| 6.3.2 | O | Flight Number | nnn(n)(a) | 800 | - | 114 |
| 6.3.4 | O | Day of Scheduled Departure | nn | 202 | - | 116 |
| 6.3.5 | O | Month of Scheduled Departure | aaa | 201 | - | 117 |
| 6.3.7 | M | Airport Code of Departure | aaa | 313 | - | 119 |
| 6.3.8 | M | Airport Code of Arrival | aaa | 313 | - | 120 |

---

## Status Details - MAN (Manifest)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 7 | O | Status Details MAN | - | - | - | 148 |
| 7.1 | M | Status Code MAN | aaa | 400 | MAN | 149 |
| 7.3.1 | O | Carrier Code | mm | 312 | - | 152 |
| 7.3.2 | O | Flight Number | nnn(n)(a) | 800 | - | 153 |

---

## Status Details - DEP (Departure)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 8 | O | Status Details DEP | - | - | - | 179 |
| 8.1 | M | Status Code DEP | aaa | 400 | DEP | 180 |
| 8.3.1 | O | Carrier Code | mm | 312 | - | 183 |
| 8.3.2 | O | Flight Number | nnn(n)(a) | 800 | - | 184 |
| 8.3.7 | M | Airport Code of Departure | aaa | 313 | - | 189 |
| 8.3.8 | M | Airport Code of Arrival | aaa | 313 | - | 190 |

---

## Status Details - PRE (Pre-Alert)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 9 | O | Status Details PRE | - | - | - | 210 |
| 9.1 | M | Status Code PRE | aaa | 400 | PRE | 211 |
| 9.3.1 | O | Carrier Code | mm | 312 | - | 214 |
| 9.3.2 | O | Flight Number | nnn(n)(a) | 800 | - | 215 |

---

## Status Details - TRM (Transhipment at Origin/Transit)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 10 | O | Status Details TRM | - | - | - | 241 |
| 10.1 | M | Status Code TRM | aaa | 400 | TRM | 242 |
| 10.3.1 | M | Carrier Code Receiving Carrier | mm | 312 | - | 245 |
| 10.3.3 | M | Airport Code of Transfer | aaa | 313 | - | 247 |

---

## Status Details - TFD (Transfer of Custody)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 11 | O | Status Details TFD | - | - | - | 255 |
| 11.1 | M | Status Code TFD | aaa | 400 | TFD | 256 |
| 11.3.1 | M | Carrier Code Receiving Carrier | mm | 312 | - | 259 |
| 11.3.3 | M | Day of Transfer | nn | 202 | - | 261 |
| 11.3.4 | M | Month of Transfer | aaa | 201 | - | 262 |
| 11.3.7 | M | Airport Code of Transfer | aaa | 313 | - | 265 |

---

## Status Details - NFD (Notification)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 12 | O | Status Details NFD | - | - | - | 282 |
| 12.1 | M | Status Code NFD | aaa | 400 | NFD | 283 |
| 12.3.1 | M | Day of Notification | nn | 202 | - | 286 |
| 12.3.2 | M | Month of Notification | aaa | 201 | - | 287 |
| 12.3.5 | M | Airport Code of Notification | aaa | 313 | - | 290 |

---

## Status Details - AWD (Award/Delivery)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 13 | O | Status Details AWD | - | - | - | 301 |
| 13.1 | M | Status Code AWD | aaa | 400 | AWD | 302 |
| 13.3.1 | M | Day of Delivery | nn | 202 | - | 305 |
| 13.3.2 | M | Month of Delivery | aaa | 201 | - | 306 |
| 13.3.5 | M | Airport Code of Delivery | aaa | 313 | - | 309 |

---

## Status Details - CCD (Customs Clearance)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 14 | O | Status Details CCD | - | - | - | 320 |
| 14.1 | M | Status Code CCD | aaa | 400 | CCD | 321 |
| 14.3.1 | M | Day of Clearance | nn | 202 | - | 324 |
| 14.3.2 | M | Month of Clearance | aaa | 201 | - | 325 |
| 14.3.5 | M | Airport Code of Clearance | aaa | 313 | - | 328 |

---

## Status Details - DLV (Delivery)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 15 | O | Status Details DLV | - | - | - | 336 |
| 15.1 | M | Status Code DLV | aaa | 400 | DLV | 337 |
| 15.3.1 | M | Day of Delivery | nn | 202 | - | 340 |
| 15.3.2 | M | Month of Delivery | aaa | 201 | - | 341 |
| 15.3.5 | M | Airport Code of Delivery | aaa | 313 | - | 344 |

---

## Status Details - DIS (Discrepancy)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 16 | O | Status Details DIS | - | - | - | 355 |
| 16.1 | M | Status Code DIS | aaa | 400 | DIS | 356 |
| 16.3.1 | O | Carrier Code | mm | 312 | - | 359 |
| 16.3.2 | O | Flight Number | nnn(n)(a) | 800 | - | 360 |
| 16.3.4 | M | Day of Discrepancy | nn | 202 | - | 362 |
| 16.3.5 | M | Month of Discrepancy | aaa | 201 | - | 363 |
| 16.3.8 | M | Airport Code of Discrepancy | aaa | 313 | - | 366 |
| 16.4.2 | M | Discrepancy Code | aaaa | 706 | - | 369 |

---

## Status Details - CRC (Customs Clearance Report)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 17 | O | Status Details CRC | - | - | - | 377 |
| 17.1 | M | Status Code CRC | aaa | 400 | CRC | 378 |
| 17.3.1 | M | Day of Reporting | nn | 202 | - | 381 |
| 17.3.2 | M | Month of Reporting | aaa | 201 | - | 382 |
| 17.3.5 | M | Airport Code of Reporting | aaa | 313 | - | 385 |

---

## Status Details - DDL (Delivery Deadline)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 18 | O | Status Details DDL | - | - | - | 403 |
| 18.1 | M | Status Code DDL | aaa | 400 | DDL | 404 |
| 18.3.1 | M | Day of Delivery | nn | 202 | - | 407 |
| 18.3.2 | M | Month of Delivery | aaa | 201 | - | 408 |
| 18.3.5 | M | Airport Code of Delivery | aaa | 313 | - | 411 |

---

## Status Details - TGC (Transfer to Ground Conveyance)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 19 | O | Status Details TGC | - | - | - | 422 |
| 19.1 | M | Status Code TGC | aaa | 400 | TGC | 423 |
| 19.3.1 | M | Day of Transfer | nn | 202 | - | 426 |
| 19.3.2 | M | Month of Transfer | aaa | 201 | - | 427 |
| 19.3.5 | M | Airport Code of Transfer | aaa | 313 | - | 430 |

---

## Status Details - ARR (Arrival)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 20 | O | Status Details ARR | - | - | - | 438 |
| 20.1 | M | Status Code ARR | aaa | 400 | ARR | 439 |
| 20.3.1 | O | Carrier Code | mm | 312 | - | 442 |
| 20.3.2 | O | Flight Number | nnn(n)(a) | 800 | - | 443 |
| 20.3.4 | M | Day of Scheduled Arrival | nn | 202 | - | 445 |
| 20.3.5 | M | Month of Scheduled Arrival | aaa | 201 | - | 446 |
| 20.3.10 | M | Airport Code of Arrival | aaa | 313 | - | 451 |

---

## Status Details - AWR (Award Received)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 21 | O | Status Details AWR | - | - | - | 471 |
| 21.1 | M | Status Code AWR | aaa | 400 | AWR | 472 |
| 21.3.1 | O | Carrier Code | mm | 312 | - | 475 |
| 21.3.2 | O | Flight Number | nnn(n)(a) | 800 | - | 476 |
| 21.3.4 | M | Day of Scheduled Arrival | nn | 202 | - | 478 |
| 21.3.5 | M | Month of Scheduled Arrival | aaa | 201 | - | 479 |
| 21.3.10 | M | Airport Code of Arrival | aaa | 313 | - | 484 |

---

## Status Details - FOH (Freight on Hand)

| Ref Num | Condition | Element Name | Data Format | Code | Fixed Value | Sort Seq |
|---------|-----------|--------------|-------------|------|-------------|---------|
| 22 | O | Status Details FOH | - | - | - | 504 |
| 22.1 | M | Status Code FOH | aaa | 400 | FOH | 505 |
| 22.3.1 | M | Day of Receipt | nn | 202 | - | 508 |
| 22.3.2 | M | Month of Receipt | aaa | 201 | - | 509 |
| 22.3.5 | M | Airport Code of Receipt | aaa | 313 | - | 512 |

---

## Additional Sections

### Other Customs Info (Section 23)
- Line Identifier: OCI
- Optional ISO Country Code
- Customs Information Identifier
- Supplementary Customs Information

### ULD Description (Section 24)
- Line Identifier: ULD
- ULD Type, Serial Number, Owner Code
- ULD Loading Indicator

### Other Service Information (Section 25)
- Line Identifier: OSI
- OSI Details with up to 65 characters

---

## Legend

| Abbreviation | Meaning |
|--------------|---------|
| M | Mandatory |
| O | Optional |
| aaa | Alphabetic field, 3 characters |
| mm | Alphanumeric field, 2 characters |
| nnn | Numeric field, 3 digits |
| n[...] | Numeric field, variable length |
| t[...] | Text field, variable length |
| Y | Check digit required |
| CRLF | Carriage Return Line Feed separator |

---

## Status Codes Reference

| Status Code | Description |
|-------------|-------------|
| RCS | Received at Sorting Center |
| RCT | Received by Transfer Carrier |
| RCF | Ready for Carriage Flight |
| BKD | Booked |
| MAN | Manifest |
| DEP | Departed |
| PRE | Pre-Alert |
| TRM | Transhipment |
| TFD | Transfer of Custody |
| NFD | Notification |
| AWD | Award/Delivery |
| CCD | Customs Clearance |
| DLV | Delivery |
| DIS | Discrepancy |
| CRC | Customs Clearance Report |
| DDL | Delivery Deadline |
| TGC | Transfer to Ground Conveyance |
| ARR | Arrival |
| AWR | Award Received |
| FOH | Freight on Hand |

