CONSOLIDATION LIST (FHL) MESSAGE
1. STANDARD MESSAGE IDENTIFIER = FHL
2. MESSAGE FUNCTION
2.1 To provide a “Check-list” of House Waybills associated with a Master Air Waybill.
2.2 (optional ) To provide details of House Waybill consignments.
3. MESSAGE APPLICATION
Computer-to-Computer.
4. MESSAGE EXCHANGE PARTIES
5. MESSAGE USE
—
6. MESSAGE EXAMPLES
6.1 Typical “Check-list” of three House Waybills associated with a Master Air Waybill.
6.2 Expanded “Check-list” of three House Waybills associated with a Master Air 
Waybill.
From: the access address of the Cargo Control Computer of the 
forwarder responsible for the Master Air Waybill.
To 
(Computer):
the access address of the Cargo Control Computer of the 
airline handling the Master Air Waybill.
Ref. Message Content
1 FHL/5
2 MBI/220-12345675FRAJFK/T1234K10000
3 HBS/11AA11111111/FRABOS/1000/K8000//NUTS
3 HBS/22AA12121212/FRAJFK/200/K1800//BOLTS
3 HBS/33AA13131313/FRAORD/34/K200//SCREWS
3 /VAL
Ref. Message Content
1 FHL/5
2 MBI/618-12345675SINJFK/T7K10000
3 HBS/AEI12345678/SINJFK/1/K400//COMPUTER PARTS
4 TXT/MODEL 3 MEMORY BOARDS AND OTHER ASSORTED PARTS

6.3 Shipper, Consignee and Char ge Declaration information for one House Waybill 
associated with a Master Air Waybill with a SLAC of 4.
7. FHL MESSAGE SPECIFICATION
Consolidation List
Cargo-IMP Manual Edition Number/Version Number
1.1 Standard Message Identifier
1.2 Separator : Slant
3 HBS/AEI12345679/SINJFK/3/K300//COMPUTER PARTS
4 TXT/MODEL 4 KEYBOARDS OTHER ASSORTED PARTS
3 HBS/AEI12345680/SINJFK/3/K300//COMPUTER PARTS
4 TXT/MODEL 5 SCREENS AND OTHER ASSORTED PARTS
Ref. Message Content
1 FHL/5
2 MBI/618-12345675SINJFK/T7K1000
3 HBS/AEI12345678/SINJFK/1/K400/4/COMPUTER PARTS
4 TXT/MODEL 3 MEMORY BOARDS AND OTHER ASSORTED PARTS
7 SHP
NAM/AIR EXPRESS INTL
ADR/CARGO COMPLEX BULDG B
LOC/AIRLINES ROAD
/SG/1738/FX/651234567
8 CNE
NAM/AIE EXPRESS INTL
ADR/CENTRAL STREET 13
LOC/JAMAICA/NY
/US/22330/TE/171812344566
9 CVD/SGD/PP/NVD/NCV/XXX
12th 16th 25th 29th 32nd
12345
1.
 Standard Message Identification
Status: 
 Note: FHL1
Status: 
 Character Format: aaa Data Element No. 101 
Status: 


1.3 Message Type Version Number
1.4 Separator : CRLF
2.1 Line Identifier
2.2 Separator : Slant
2.3 Master AWB Identification
2.3.1 Airline Prefix
2.3.2 Separator : Hyphen
2.3.3 AWB Serial Number
2.4 AWB Origin and Destination
2.4.1 Airport/City Code (of Origin)
2.4.2 Airport/City Code (of Destination)
2.5 Quantity Detail
2.5.1 Separator : Slant
2.5.2 Shipment Description Code (T)
2.5.3 Number of Pieces
2.5.4 Weight Code
2.5.5 Weight
2.6 Separator : CRLF
Status: 
 Character Format: n[...3] Data Element No. 124 
Status: 
2.
 Master AWB Consignment Detail
Status: 
Status: 
 Character Format: aaa Data Element No. 103 
Status: 
Status: 
Status: 
 Character Format: nnn Data Element No. 112 
Status: 
Status: 
 Character Format: n[8] Data Element No. 113 
Status: 
Status: 
 Character Format: aaa Data Element No. 313 
Status: 
 Character Format: aaa Data Element No. 313 
Status: 
Status: 
Status: 
 Character Format: a Data Element No. 703 
Status: 
 Character Format: n[...4] Data Element No. 701 
Status: 
 Character Format: a Data Element No. 601 
Status: 
 Character Format: n[...7]p Data Element No. 600 
Status: 
3.
 House Waybill Summary Details
Status: 


3.1 Line Identifier
3.2 Separator : Slant
3.3 HWB Serial Number
3.4 Separator : Slant
3.5 House Waybill Origin and Destination
3.5.1 Airport/City Code (of Departure)
3.5.2 Airport/City Code (of Destination)
3.6 Separator : Slant
3.7 House Waybill Totals
3.7.1 Number of Pieces
3.7.2 Separator : Slant
3.7.3 Weight Code
3.7.4 Weight
3.7.5 Separator : Slant
3.7.6 SLAC
3.8 Nature of Goods
3.8.1 Separator : Slant
3.8.2 Manifest Description of Goods
3.9 Separator : CRLF
3.10 Special Handling Requirements
3.10.1 Separator : Slant
Status: 
 Character Format: aaa Data Element No. 103 
Status: 
Status: 
 Character Format: m[1...12] Data Element No. 119 
Status: 
Status: 
Status: 
 Character Format: aaa Data Element No. 313 
Status: 
 Character Format: aaa Data Element No. 313 
Status: 
Status: 
Status: 
 Character Format: n[...4] Data Element No. 701 
Status: 
Status: 
 Character Format: a Data Element No. 601 
Status: 
 Character Format: n[...7]p Data Element No. 600 
Status: 
Status: 
 Character Format: n[...5]
Status: 
Status: 
Status: 
 Character Format: t[...15] Data Element No. 708 
Status: 
 Note: FHL29
Status: 


3.10.2 Special Handling Code
Element 3.10 can be repeated. Can occur a maximum of nine times.
3.11 Separator : CRLF
Ref. 3 can be repeated.
4.1 Line Identifier
4.2 Separator : Slant
4.3 Free Text
4.4 Separator : CRLF
Elements 4.2 thru 4.4 can be repeated. Can occur a maximum of nine times.
5.1 Line Identifier
5.2 Separator : Slant
5.3 Harmonised Commodity Code
5.4 Separator : CRLF
Elements 5.2 to 5.4 can be repeated. Can occur a maximum of nine times.
6.1 Line Identifier (OCI)
6.2 Separator : Slant
6.3 ISO Country Code
6.4 Separator : Slant
Status: 
Status: 
 Character Format: aaa Data Element No. 705 
Status: 
4.
 Free Text Description of Goods
Status: 
 Note: FHL20
Status: 
 Character Format: aaa Data Element No. 103 
Status: 
Status: 
 Character Format: t[...65] Data Element No. 127 
Status: 
5.
 Harmonised Tariff Schedule Information
Status: 
 Note: FHL28
Status: 
 Character Format: aaa Data Element No. 103 
Status: 
Status: 
 Character Format: m[6...18] Data Element No. 900 
Status: 
6.
 Other Customs, Security and Regulatory Control Information
Status: 
 Note: FHL2
Status: 
 Character Format: aaa Data Element No. 103 
Status: 
Status: 
 Character Format: aa Note: FHL30 Data Element No. 304 


6.5 Information Identifier
6.6 Separator : Slant
6.7 Customs, Security and Regulatory Control Information Identifier
6.8 Separator : Slant
6.9 Supplementary Customs, Security and Regulatory Control Information
6.10 Separator : CRLF
Elements 6.2 to 6.10 can be repeated
Ref. 3 thru 6 can be repeated if there is no occurrence of Ref. 7, 8 or 9.
7.1 Line Identifier
7.2 Separator : CRLF
7.3 Name
7.3.1 Information Identifier (NAM)
7.3.2 Separator : Slant
7.3.3 Name
7.3.4 Separator : CRLF
Elements 7.3.2 thru 7.3.4 can be repeated. Can occur a maximum of two times.
7.4 Street Address
7.4.1 Information Identifier (ADR)
7.4.2 Separator : Slant
7.4.3 Street Address
Status: 
Status: 
 Character Format: aaa Note: FHL30 Data Element No. 103 
Status: 
Status: 
 Character Format: a[...2] Note: FHL30 Data Element No. 941 
Status: 
Status: 
 Character Format: t[...35] Data Element No. 940 
Status: 
7.
 Shipper Name and Address
Status: 
Status: 
 Character Format: aaa Data Element No. 103 
Status: 
Status: 
Status: 
 Character Format: aaa Data Element No. 103 
Status: 
Status: 
 Character Format: t
[...35]
HWB Box: 
4
Data Element No. 
300 
Status: 
Status: 
Status: 
 Character Format: aaa Data Element No. 103 
Status: 


7.4.4 Separator : CRLF
Elements 7.4.2 thru 7.4.4 can be repeated. Can occur a maximum of two times.
7.5 Location
7.5.1 Information Identifier (LOC)
7.5.2 Separator : Slant
7.5.3 Place
7.5.4 Separator : Slant
7.5.5 State/Province
7.5.6 Separator : CRLF
7.6 Coded Location
7.6.1 Separator : Slant
7.6.2 ISO Country Code
7.6.3 Separator : Slant
7.6.4 Post Code
7.7 Contact Detail
7.7.1 Separator : Slant
7.7.2 Contact Identifier
7.8.3 Separator : Slant
7.8.4 Contact Number
Element 7.8 can be repeated.
7.9 Separator : CRLF
Status: 
 Character Format: t
[...35]
HWB Box: 
4
Data Element No. 
301 
Status: 
Status: 
Status: 
 Character Format: aaa Data Element No. 103 
Status: 
Status: 
 Character Format: t[...17] Data Element No. 302 
Status: 
 Note: FHL21
Status: 
 Character Format: t[...9] Data Element No. 303 
Status: 
Status: 
 Note: FHL22
Status: 
Status: 
 Character Format: aa Data Element No. 304 
Status: 
 Note: FHL23
Status: 
 Character Format: t[...9] Data Element No. 305 
Status: 
 Note: FHL22
Status: 
Status: 
 Character Format: m[...3] Data Element No. 122 
Status: 
Status: 
 Character Format: m[...25] Data Element No. 123 


8.1 Line Identifier
8.2 Separator : CRLF
8.3 Name
8.3.1 Information Identifier (NAM)
8.3.2 Separator : Slant
8.3.3 Name
8.3.4 Separator : CRLF
Elements 8.3.2 thru 8.3.4 can be repeated. Can occur a maximum of two times.
8.4 Street Address
8.4.1 Information Identifier (ADR)
8.4.2 Separator : Slant
8.4.3 Street Address
8.4.4 Separator : CRLF
Elements 8.4.2 thru 8.4.4 can be repeated. Can occur a maximum of two times.
8.5 Location
8.5.1 Information Identifier (LOC)
8.5.2 Separator : Slant
8.5.3 Place
8.5.4 Separator : Slant
Status: 
8.
 Consignee Name and Address
Status: 
 Note: FHL24
Status: 
 Character Format: aaa Data Element No. 103 
Status: 
Status: 
Status: 
 Character Format: aaa Data Element No. 103 
Status: 
Status: 
 Character Format: t
[...35]
HWB Box: 
4
Data Element No. 
300 
Status: 
Status: 
Status: 
 Character Format: aaa Data Element No. 103 
Status: 
Status: 
 Character Format: t
[...35]
HWB Box: 
4
Data Element No. 
301 
Status: 
Status: 
Status: 
 Character Format: aaa Data Element No. 103 
Status: 
Status: 
 Character Format: t[...17] Data Element No. 302 
Status: 
 Note: FHL25

8.5.5 State/Province
8.5.6 Separator : CRLF
8.7 Coded Location
8.7.1 Separator : Slant
8.7.2 ISO Country Code
8.7.3 Separator : Slant
8.7.4 Post Code
8.8 Contact Detail
8.8.1 Separator : Slant
8.8.2 Contact Identifier
8.8.3 Separator : Slant
8.8.4 Contact Number
Element 8.8 can be repeated.
8.9 Separator : CRLF
9.1 Line Identifier
9.2 Separator : Slant
9.3 ISO Currency Code
9.4 Separator : Slant
9.5 Prepaid/Collect Charge Declarations
9.5.1 P/C Ind. (Weight/Valuation)
Status: 
 Character Format: t[...9] Data Element No. 303 
Status: 
Status: 
 Note: FHL26
Status: 
Status: 
 Character Format: aa Data Element No. 304 
Status: 
 Note: FHL27
Status: 
 Character Format: t[...9] Data Element No. 305 
Status: 
 Note: FHL26
Status: 
Status: 
 Character Format: m[...3] Data Element No. 122 
Status: 
Status: 
 Character Format: m[...25] Data Element No. 123 
Status: 
9.
 Charge Declarations
Status: 
Status: 
 Character Format: aaa Data Element No. 103 
Status: 
Status: 
 Character Format: aaa Data Element No. 606 
Status: 
Status: 


9.5.2 P/C Ind. (Other Charges)
9.6 Value for Carriage Declaration
9.6.1 Separator : Slant
9.6.2 Declared Value for Carriage
9.7 Value for Customs Declaration
9.7.1 Separator : Slant
9.7.2 Declared Value for Customs
9.8 Value for Insurance Declaration
9.8.1 Separator : Slant
9.8.2 Declared Value for Insurance
9.9 Separator : CRLF
8. MESSAGE NOTES 
Status: 
 Character Format: a Data Element No. 403 
Status: 
 Character Format: a Data Element No. 403 
Status: 
Status: 
Status: 
 Character Format: n[...12]p Data Element No. 510 
or
No Value Declared (NVD)
Character Format: aaa
Status: 
Status: 
Status: 
 Character Format: n[...12]p Data Element No. 509 
or
No Customs Value (NCV)
Character Format: aaa
Status: 
Status: 
Status: 
 Character Format: n[...11]p Data Element No. 508 
or
No Value (XXX)
Character Format: aaa
Status: 
FHL1 Ref. 1 For a multi-part FHL message that breaks in the middle of House 
Waybill data, subsequent parts must also include the previous 
occurrence of Ref. 3
 following the standard previous SMI and first 
line of SMT to correctly associ ate the data with the appropriate 
House Waybill and Master Air Waybill.

8.8.1 OCI composition rules table
FHL2 Ref. 6. Other Customs, Security and Regulatory Control Information
The composition of the OCI line depends upon  which Customs, 
Security and Regulatory Control Information Identifier is used and 
must be in accordance with the OCI composition rules table 
below.
FHL20 Ref. 4. Free Text Description of Goods  (when interchanging with US 
Customs, the total characters of Ref. 4 cannot exceed 545).
FHL21 Ref. 
7.5.4
Separator (if 7.5.5 included).
FHL22 Ref. 
7.6
Coded Location
Ref. 
7.7
Contact Details
(total characters of 7.6 through 7.7 cannot exceed 69).
FHL23 Ref. 
7.6.3
Separator (if 7.6.4 and/or 7.7 included).
FHL24 Ref. 8. Consignee Name and Address (if Ref. 7 included).
FHL25 Ref. 
8.5.4
Separator (if 8.5.5 included).
FHL26 Ref. 
8.7
Coded Location
Ref. 
8.8
Contact Detail
(total characters of 8.7 through 8.8 cannot exceed 69).
FHL27 Ref. 
8.7.3
Separator (if 8.7.4 and/or 8.8 included).
FHL28 Ref. 5 Harmonised Tariff Schedule Info rmation May only be included as 
respective, additional information to Ref. 4 Free Text Description 
of Goods.
FHL29 Ref. 
3.9
Separator (if 3.10 included).
FHL30 Ref. 
6.3
ISO Country Code
Ref. 
6.5
Information Identifier
Ref. 
6.7
Customs Information Identifier
(At least one of Ref. 6.3., Ref. 6.5. or Ref. 6.7. must be included).
ISO Information Customs, Explanat ory notes on allowed values for 

Country 
Code 
Identifier Security 
and 
Regulatory 
Control 
Information 
Identifier 
the Information Identifier and completion 
examples. Any Screening Method, 
Screening Exemption or Security Status 
codes are to be included in the 
Supplementary Customs, Security and 
Regulatory Control Information and not 
in the Information Identifier. 
AC If following an RA entry: 
OCI/GB/ISS/RA/001-011
///ED/0213
///AC/12345ABCDE
If only the AC entry: 
OCI///AC/12345ABCDE
ME OCI/GB//E/12345ABCDE
M M A AGT - agent subm itting house details to 
USA 
OCI/US/AGT/A/12345678
M C DOC - certificate identifier 
OCI//DOC/C/12345678
M D DNR – UNID (the FDD message also 
contains this information and more) 
OCI//DNR/D/UN1234 UN2345 UN3456 
UN4567 UN6789
//DNR/D/UN8901 ID8000
DOC - shippers declaration identifier 
OCI//DOC/D/12345678
L Screening Exemption Codes are to be 
included in the Supplementary Customs & 
Security Control Information 
SMUS - small undersized shipments 
MAIL - mail 
BIOM - bio-medical samples 
DIPL - diplomatic bags or diplomatic mail 
LFSM - life-saving materials 
NUCL - nuclear materials 
TRNS - transfer or transhipment 
OCI/GB/ISS/RA/001-011
///ED/0213
///L/DIPL

M V DOC - invoice identifier 
OCI//DOC/V/12345678
M I HWB – house waybill number 
MAL – mail receptacle number 
ULD – unit load device identifier 
If indicating an MRN for a HWB level 
OCI/IT/IMP/M/07IT9876AB88901235
//HWB/I/XXX12345678
If indicating an MRN for a HWB within a 
ULD 
OCI/IT/IMP/M/07IT9876AB88901235
//HWB/I/XXX12345678
//ULD/I/A1A12345XX
M M F AGT - agent submitti ng house details to the 
USA 
TID - local transfer as destination in the 
USA 
OCI/US/TID/F/12345678
MK C OCI/GB//KC/001-011
///ED/0213
M M M IMP – Customs import 
EXP – Customs export 
TRA – Customs transit 
OCI/IT/IMP/M/07IT9876AB88901235
M P DOC – packing list identifier 
OCI//DOC/P/12345678
RC OCI/FR//RC/Dest Country Dest Airport-
Regulated Carrier Name 
Example 
OCI/FR//RC/NGLOS-AF
M M RA ISS - the regulat ed agent issuing the 
security status 
OCI/GB/ISS/RA/001-011
///ED/0213
OSS - the regulated agent accepting the 
security status given by another regulated 
agent 

OCI/GB/ISS/RA/001-011
///ED/0213
/GB/OSS/RA/002-022
///ED/0213
N Can only follow an entry  identifying a ULD 
ULD – number of a seal affixed to a unit 
load device 
OCI//ULD/I/A1A12345XX
///N/1234567890
MS OCI/US//S/SYSTEM DOWN 0000-0030 
05MAR10
M M T AGT - Agent’s valid trader identification 
number can be indicated 
If in Canada and a third party lodges the 
declaration to Canada: 
OCI/CA/AGT/T/8000
DCL - Declarant’s (Legal person/entity 
lodging the declaration) valid trader 
identification number can be indicated 
If in the EU the EORI of the declaring 
lodging the ENS shall be indicated: 
OCI/GB/DCL/T/GB123456789012
SHP - Consignor’s valid trader identification 
number can be indicated 
CNE - Consignee’s valid trader 
identification number can be indicated 
BRK - Broker’s valid trader identification 
number can be indicated 
AIR - Airline’s valid trader identification 
number can be indicated 
NFY - Notify party’s valid trader 
identification number can be indicated 
MU OCI/KE//U/KE1234567890
ED Must follow RA or KC entry as 
OCI/GB//KC/001-011
///ED/0213
SM Can only follow RA en try Screening Method 
Codes are to be included in the 
Supplementary Customs & Security Control 

Information 
PHS – Physical Inspection and/or hand 
search 
VCK - Visual check 
XRY - X-ray equipment 
EDS - Explosive detection system 
RES - Remote explosive scent tracing 
explosive detection dogs 
FRD - Free running explosive detection 
dogs 
VPT - Vapor trace 
PRT - Particle trace 
MDE - Metal Detection Equipment 
SIM - Subjected to flight simulation 
AOM - Subjected to any other means 
OCI/GB/ISS/RA/001-011
///ED/0213
///SM/RES
///SM/AOM-SPECIFY ANY OTHER 
MEANS
SD Can only follow RA  entry and screening 
method or exemption 
OCI/GB/ISS/RA/001-011
///ED/0213
///SM/RES
///SD/05MAR122359
SN Can only follow RA  entry and screening 
method or exemption 
OCI/GB/ISS/RA/001-011
///ED/0213
///SM/RES
///SN/JOHNNY WALKER
///SD/05MAR122359
SS Only applicable for the FSA/FSU message. 
All other messages shall capture this as a 
SPH code.
Only one SS code can be entered 
SCO *can only follow RA entry 
SPX *can only follow RA entry 
NSC 

9. CONSOLIDATION LIST MESSAGE LAYOUT
OCI/GB/ISS/RA/001-011
///ED/0213
///SS/SPX
ST To capture any ad ho c security statement 
required by regulators 
OCI/GB/ISS/RA/001-011
///ED/0213
///ST/THIS MASTER AIR WAYBILL 
CONTAINS NO
///ST/1. FREIGHT FROM THAT 
COUNTRY
///ST/2. TONER CARTRIDGE 
GREATER THAN 550
///ST/ GRAMS TRANSFERRING THIS 
COUNTRY