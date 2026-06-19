Data Element Grid

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
100
Message 
Sequence 
Number
A sequential number used in 
messages where the contents of 
one logical message can exceed 
the physical limit
n[...2] 4
Sub Element ID Format Description
100D001 n[...2] Message Sequence Number
101
Standard 
Message 
Identifier
Code shown at the beginning of 
all standard messages to 
uniquely identify a given type of 
message
aaa FSR 1.17
Sub Element ID Format Description
101D001 aaa Standard Message Identifier
102 End of Message 
Code
Code indicating the “end of 
message part” or “end of total 
message”. Used in messages 
where the contents of one 
logical message can exceed the 
physical limit
aaaa CONT 1.9
Sub Element ID Format Description
102D001 aaaa End of Message Code
103 Line Identifier Information 
Identifier
Code identifying a particular 
group of data elements
aaa CNE 1.19
Sub Element ID Format Description
103D001 aaa Line Identifier
104 —
Intentionall
y Left Blank
105 AWB Column 
Identifier
HWB Column 
Identifier
Coded identification of a column 
within the tariff/description 
section on the Air Waybill
a R 1.32
Sub Element ID Format Description
105D001 a AWB Column Identifier (P)
105D002 a AWB Column Identifier (K or L)
105D003 a AWB Column Identifier (C)
105D004 a AWB Column Identifier (S)
105D005 a AWB Column Identifier (W)
105D006 a AWB Column Identifier (R)
105D007 a AWB Column Identifier (T)
105D008 a AWB Column Identifier (N)
106 AWB Rate Line 
Number
HWB Rate 
Line Number
Number to identify each tariff 
line in the tariff/description 
section of the Air Waybill
n[...2] 2
Sub Element ID Format Description
106D001 n[...2] AWB Rate Line Number
107 Office Function 
Designator
Code identifying an office for 
addressing purposes
mm 6F 1.34
Sub Element ID Format Description
107D001 aa Office Function Designator
108 Account 
Number
Coded identification of a 
participant
t[...14] ABC94269
Sub Element ID Format Description
108D001 t[...14] Account Number
109 Telephone 
Number
Telephone contact of a 
participant
t[...14] 514 844 6311
Sub Element ID Format Description
109D001 t[...14] Telephone Number

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
110 
Intentionall
y Left Blank
111 Embargo 
Number
Identification number allocated 
to each embargo by originating 
airline
n[...3] 173
Sub Element ID Format Description
111D001 n[...3] Embargo Number
112 Airline Prefix
AWB Prefix, 
Airline Code 
Number
Coded representation of an 
airline
nnn 057 See IATA Airline Coding 
Directory.
Sub Element ID Format Description
112D001 nnn Airline Prefix
113 AWB Serial 
Number
Shipment 
Reference 
Number
A serial number allocated by an 
airline to identify a particular air 
cargo shipment and the 
associated Air Waybill
n[8] 12345675
Last digit of number is 
unweighted modulus 7 
check digit as specified in 
CSC, Resolution 600a.
Sub Element ID Format Description
113D001 n[8] AWB Serial Number
114 CCA Serial 
Number
Identification number allocated 
to each Cargo Charges 
Correction Advice
mnnnnn C12345
Sub Element ID Format Description
114D001 mnnnnn CCA Serial Number
115 ULD Serial 
Number
Serial number allocated to each 
Unit Load Device by its owner
mnnn(n) 1234
The three possible 
representations of the 
format shall be mnnn, 
mnnnn, nnnn or nnnnn
Sub Element ID Format Description
115D001 mnnn(n) ULD Serial Number
116 —
Intentionall
y Left Blank
117 Booking File 
Reference
File 
Reference
A reference used to identify a 
specific booking or file t[...15] 123456
For CASS EDI messsages 
the maximum number of 
characters is 14
Sub Element ID Format Description
117D001 t[...15] Booking File Reference
117D002 t[...15] File Reference
118
Transfer 
Manifest 
Number
Substitute 
Flight 
Manifest 
Number
Identification number allocated 
to each transfer manifest or 
substitute flight manifest
n[6] 123456
Sub Element ID Format Description
118D001 n[6] Transfer Manifest Number
119 HWB Serial 
Number
A serial number allocated by an 
agent/consolidator to identify a 
particular air cargo shipment 
within a Master Air Waybill
m[1...12] 12345678ABCD
Sub Element ID Format Description
119D001 m[1...12] HWB Serial Number
120 Master AWB 
Indicator
Code identifying a Master Air 
Waybill
a M 1.35
Sub Element ID Format Description
120D001 a Master AWB Indicator
121 Transfer/Transit 
Control Number
Control number allocated to a 
shipment when other than the 
air waybill number will be used 
for control of in-bond shipments
t[...12] IT1234578

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
121D001 t[...12] Transfer/Transit Control Number
122 Contact 
Identifier
Code identifying a means of 
contact for a participant m[...3] TE 1.39
Although the format allows 
for up to three alpha-
numeric codes, currently 
the only valid contact 
identifiers are FX, TE and 
TL.
Sub Element ID Format Description
122D001 m[...3] Contact Identifier
123 Contact Number Contact Number of a participant m[...25] 5148446311
Sub Element ID Format Description
123D001 m[...25] Contact Number
124 Message Type 
Version Number
Version number of a message 
type n[...3] 1 General Information, 15
Sub Element ID Format Description
124D001 n[...3] Message Type Version Number
125 Text Subject 
Qualifier
Code identifying a type of free 
text information
mmm ING 1.77
Sub Element ID Format Description
125D001 mmm Text Subject Qualifier
126 Text Reference Coded reference of the party 
responsible for the message
mmm REU
Sub Element ID Format Description
126D001 mmm Text Reference
127 Free Text Information presented as free 
text
t[...65] SYSTEM CLOSED 
01-02 AM UTC
Sub Element ID Format Description
127D001 t[...65] Free Text
128 HWB as agreed Coded representation of the 
statement “as agreed”
a A 1.81
Sub Element ID Format Description
128D001 a HWB as agreed
129 —
Intentionall
y Left Blank
130
Application 
Reference 
Number
Reference number allocated for 
an application
t[...35] SRN123 ABC
Sub Element ID Format Description
130D001 t[...35] Application Reference Number
131 Identification 
Number
Number identifying a Debit or 
Credit Memorandum, or a 
Charges Correction Advice
n[...8] 12345678
Sub Element ID Format Description
131D001 n[...8] Identification Number
132 Reference 
Number
Reference number allocated to 
a consignment as per 
shipper/agent/issuing carrier 
agreement
t[...14] ABCD-12345
Sub Element ID Format Description
132D001 t[...14] Reference Number
133
Supplementary 
Shipment 
Information
Additional shipment information 
that supplements the reference 
number
t[...12] COMPANY MAT
Sub Element ID Format Description

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
133D001 t[...12] Supplementary Shipment Information
134 Vehicle Booking 
Reference
Reference number allocated to 
the booking of a terminal 
loading dock slot for a vehicle
m[...8] VBRN0013
Sub Element ID Format Description
134D001 m[...8] Vehicle Booking Reference
135 Vehicle Plate 
Number
The number that appears on a 
vehicle licence plate
t[...10] 800 CKG
Sub Element ID Format Description
135D001 t[...10] Vehicle Plate Number
136 AWB Individual 
Piece Number
Number identifying a particular 
piece of an air waybill 
consignment
n[4] 0010
Sub Element ID Format Description
136D001 n[4] AWB Individual Piece Number
137 HWB Individual 
Piece Number
Number identifying a particular 
piece of a house waybill 
consignment
n[4] 0005
Sub Element ID Format Description
137D001 n[4] HWB Individual Piece Number
138
Piece 
Identification 
Indicator
Code indicating whether or not 
unique piece identification 
numbers have been assigned, 
included, are available upon 
request or required.
a A 1.97
Sub Element ID Format Description
138D001 a Unique Piece Identification Indicator
139 Unique Piece 
Number
Number uniquely identifying a 
shipper’s particular piece
t[...35] 0010
Sub Element ID Format Description
139D001 t[...35] Unique Piece Number
140 Voucher Serial 
Number
Number identifying a particular 
courier baggage voucher
m[1...12] ABCD1234
Sub Element ID Format Description
140D001 m[1...12] Voucher Serial Number
141 Ticket Number Passenger ticket number n[13...15] 0146778741203
Sub Element ID Format Description
141D001 n[13...15] Ticket Number
142 Bag Tag Number
Sequential number portion of 
the baggage tag identifying a 
passenger or courier bag
n[8...10] 0012345678
Sub Element ID Format Description
142D001 n[8...10] Bag Tag Number
200 Year Last two digits of year nn 88
Sub Element ID Format Description
200D001 nn Year
200D002 nn Year (of Issue)
201 Month The first three letters of the full 
English name of a month
aaa SEP 1.11
Sub Element ID Format Description
201D001 aaa Month
201D002 aaa Month (of Scheduled Departure)
201D003 aaa Month (of Transfer)
201D004 aaa Month (of Delivery)

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
201D005 aaa Month (of Arrival)
201D006 aaa Month (of Notification)
201D007 aaa Month (of Departure)
201D008 aaa Month (of Receipt)
201D009 aaa Month (of Clearance)
201D010 aaa Month (of Discrepancy)
201D011 aaa Month (of Issue)
201D012 aaa Month (of Scheduled Arrival)
201D013 aaa Month (of Consignment Ready)
201D014 aaa Month (of Requested Delivery)
202 Day of Month Numeric representation of a day 
in a month nn 04
Sub Element ID Format Description
202D001 nn Day
202D002 nn Day of Month
202D003 nn Day (of Scheduled Departure)
202D004 nn Day (of Transfer)
202D005 nn Day (of Delivery)
202D006 nn Day (of Arrival)
202D007 nn Day (of Notification)
202D008 nn Day (of Departure)
202D009 nn Day (of Receipt)
202D010 nn Day (of Clearance)
202D011 nn Day (of Discrepancy)
202D012 nn Day (of Issue)
202D013 nn Day (of Scheduled Arrival)
202D014 nn Day (of Consignment Ready)
202D015 nn Day (of Requested Delivery)
203 Time Actual Time 24 hours representation in 
hours and minutes
nnnn 1323 Either local time or UTC
Sub Element ID Format Description
203D001 nnnn Time
203D002 nnnn Time (of Transfer)
203D003 nnnn Time (of Delivery)
203D004 nnnn Time (of Departure)
203D005 nnnn Time (of Arrival)
203D006 nnnn Time (of Scheduled Departure)
203D007 nnnn Time (of Scheduled Arrival)
203D008 nnnn Actual Time (of Given Status Event)
203D009 nnnn Time (of Consignment Ready)
203D010 nnnn Time (of Shipper Close)
203D011 nnnn Time (of Requested Delivery)
203D012 nnnn Time (of Consignee Open)
204 Day of the Week Numeric representation of a day 
within a week
n 1 1.40
Sub Element ID Format Description

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
204D001 n Day of the Week
205 Day Change 
Indicator
Code indicating day changes 
between particular events a N 1.41
Sub Element ID Format Description
205D001 a Day Change Indicator
206 Type of Time 
Indicator
Code indicating the type of 
Time
a S 1.51
Sub Element ID Format Description
206D001 a Type of Time Indicator
207
Type of 
Information 
Indicator
Coded indication of the type of 
information requested or 
exchanged
a H 1.88
Sub Element ID Format Description
207D001 a Type of Information Indicator
208 Century The century portion of a year nn 20
Sub Element ID Format Description
208D001 nn Century
209 Seconds Seconds of a minute nn 12
Sub Element ID Format Description
209D001 nn Seconds
300 Name
Identification of individual or 
company involved in the 
movement of a consignment
t[...35] ACE SHIPPING 
CO.
Sub Element ID Format Description
300D001 t[...35] Name
301 Street Address
Street address of individual or 
company involved in the 
movement of a consignment
t[...35] 14 WIGMORE 
STREET
Sub Element ID Format Description
301D001 t[...35] Street Address
302 Place
Location of individual or 
company involved in the 
movement of a consignment
t[...17] LONDON
Sub Element ID Format Description
302D001 t[...17] Place
302D002 t[...17] Place (of Issue)
302D003 t[...17] Place (of Origin)
302D004 t[...17] Place (of Destination)
303 State/Province
Part of a country of an 
individual or company involved 
in the movement of a 
consignment
t[...9] QUE
Sub Element ID Format Description
303D001 t[...9] State/Province
304 ISO Country 
Code
Coded representation of a 
country approved by ISO
aa CH See IATA Airline Coding 
Directory.
Sub Element ID Format Description
304D001 aa ISO Country Code
304D002 aa ISO Country Code (of Coding Country)
305 Post Code Zip Code
Code allocated by national 
postal authority to identify 
location for mail delivery 
purposes
t[...9] H3A 2R4
Sub Element ID Format Description

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
305D001 t[...9] Post Code
306 —
Intentionall
y Left Blank
307 ICAO Carrier 
Code
ICAO Airline 
Designator
Coded Identification approved 
by ICAO for a carrier aaa AFR
Does not correspond to 
data element 312 — Carrier 
Code.See IATA Airline 
Coding Directory.
Sub Element ID Format Description
307D001 aaa ICAO Carrier Code
307D002 aaa ICAO Carrier Code (of onward carrier)
308 Company 
Designator
Code identifying a company for 
addressing purposes
mm XB
Actual format is “aa”, “na” 
or “an”.See IATA Airline 
Coding Directory.
Sub Element ID Format Description
308D001 mm Company Designator
309
IATA Cargo 
Agent CASS 
Address
Code issued by IATA to identify 
individual agent locations for 
CASS billing purposes
nnnn 1234
Only occurs in addition to 
data element 311.Last digit 
is unweighted modulus 7 
check digit of data element 
311 and first 3 digits of data 
element 309.
Sub Element ID Format Description
309D001 n[4] IATA Cargo Agent CASS Address
310 Abbreviated 
Name Short Name Abbreviation of a participant 
name sufficient for identification t[...17] LANDSEAIR
Sub Element ID Format Description
310D001 t[...17] Abbreviated Name
311
IATA Cargo 
Agent Numeric 
Code
Code issued by IATA to identify 
each IATA Cargo Agent whose 
name is entered on the Cargo 
Agency List
n[7] 1234567
Sub Element ID Format Description
311D001 n[7] IATA Cargo Agent Numeric Code
312 Carrier Code Airline 
Designator
Coded identification approved 
by IATA for a carrier
mm BA
Actual format is “aa”, “an” 
or “na”.See IATA Airline 
Coding Directory.
Sub Element ID Format Description
312D001 mm Carrier Code
312D002 mm Carrier Code (of Next Carrier)
312D003 mm Carrier Code (Transferred to)
312D004 mm Carrier Code (Transferring Carrier)
312D005 mm Carrier Code (Receiving Carrier)
313 Location 
Identifier
Airport/City 
Code
Coded representation of a 
specific airport/city code
aaa LHR
Future plans to move to 4 
or 5 alpha airport/city 
code.See IATA Airline 
Coding Directory.
Sub Element ID Format Description
313D001 aaa Airport/City Code (of Origin)
313D002 aaa Airport/City Code (of Destination)
313D003 aaa Airport/City Code (of Departure)
313D005 aaa Airport Code (of Departure)
313D006 aaa Airport Code (of Arrival)
313D007 aaa Airport/City Code

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
313D008 aaa Airport/City Code (of 1st Destination)
313D009 aaa Airport/City Code (of Next Destination)
313D010 aaa Airport Code (of Receipt)
313D011 aaa Airport Code (of Transfer)
313D012 aaa Airport Code (of Notification)
313D013 aaa Airport Code (of Unloading)
313D014 aaa Airport Code (of Loading)
313D015 aaa Airport Code (of Delivery)
313D021 aaa Airport Code (of Clearance)
313D022 aaa Airport Code (of Discrepancy)
313D023 aaa Airport/City Code (of Issue)
313D024 aaa Airport Code
313D025 aaa City Code (of Origin)
313D026 aaa City Code (of Destination)
313D027 aaa Airport Code (of 1st Entry Point)
313D028 aaa Airport/City Code (Customs Clearance)
314 —
Intentionall
y Left Blank
315 Entitlement 
Code
Coded identification of the 
recipient of a charge amount a C 1.3
Sub Element ID Format Description
315D001 a Entitlement Code
316
Rate 
Combination 
Point
RCP Point over which sector rates 
are combined
aaa PAR
See IATA Airline Coding 
Directory.Must be a city 
code.
Sub Element ID Format Description
316D001 aaa Rate Combination Point
317 Broker/Consolid
ator Code
Code identifying a particular 
Broker/Consolidator
t[...7] ABTRANS
318 Cargo Terminal 
Operator ID
Identification of an operator 
controlling a Cargo Terminal
m[...7] DLH
319 Participant 
Identifier
Code identifying the type of 
participant involved in the 
movement of a shipment
m[...3] CNE 1.36
Sub Element ID Format Description
319D001 m[...3] Participant Identifier
320 Participant Code
Coded identification of a 
participant involved in the 
movement of a shipment
m[...17] 98764
Sub Element ID Format Description
320D001 m[...17] Participant Code
321
Bonded 
Premises 
Identification
Coded identification of the 
warehouse where a bonded 
shipment will be stored
m[...7] 96763
Sub Element ID Format Description
321D001 m[...7] Bonded Premises Identification
321D002 m[...7] Bonded Premises Location
322 Number of 
Stops
Value indicating the number of 
stops on a flight n 2
Sub Element ID Format Description
322D001 n Number of Stops

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
323 Vehicle 
Operator
The party responsible for the 
operation of a vehicle t[...17] GLENGARRY
Sub Element ID Format Description
323D001 t[...17] Vehicle Operator
324 Driver ID Identification of the driver of a 
vehicle
t[...10] A-09876
Sub Element ID Format Description
324D001 t[...10] Driver ID
325 Number of 
Passengers
The number of passengers 
accompanying the driver of a 
vehicle
n 1
Sub Element ID Format Description
325D001 n Number of Passengers
326
Cargo Terminal 
Bay 
Identification
Identification of a cargo 
terminal bay for a vehicle
t[...7] BAY10
Sub Element ID Format Description
326D001 t[...7] Cargo Terminal Bay Identification
327 Courier Service 
Provider
Coded identification of a courier 
service provider
m[...4] AB12 The three digit IATA Airline 
Prefix may be used
Sub Element ID Format Description
327D001 m[...4] Courier Service Provider
400 Status Code Coded representation of the 
current status of a consignment
aaa DEP 1.18
Sub Element ID Format Description
400D001 aaa Status Code
401 Change Code Coded Identification of the type 
of a change
aa AD 1.10
Sub Element ID Format Description
401D001 aa Change Code
402 Nil Cargo Code Code indicating that no cargo 
has been loaded on a flight
aaa NIL 1.13
Sub Element ID Format Description
402D001 aaa Nil Cargo Code
403 P/C Ind. Prepaid/Colle
ct Indicator
Code indicating whether 
payment will be made at origin 
(prepaid) or at destination 
(collect)
a P 1.5
Sub Element ID Format Description
403D001 a P/C Ind. (Weight/Valuation)
403D002 a P/C Ind. (Other Charges)
403D003 a Prepaid/Collect Indicator (P or C)
404 Special Service 
Request
Information related to 
instructions for special action 
required
t[...65]
MUST BE KEPT 
ABOVE 5 
DEGREES 
CELSIUS
Sub Element ID Format Description
404D001 t[...65] Special Service Request
405 Other Service 
Information Remarks relating to a shipment t[...65]
EXTRA CHARGE 
DUE TO 
SPECIAL 
HANDLING 
REQUIREMENTS
Sub Element ID Format Description
405D001 t[...65] Other Service Information
406 Embargo Detail Details relating to embargoes t[...65] NO AVI 
FACILITIES

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
406D001 t[...65] Embargo Detail
407 —
Intentionall
y Left Blank
408 —
Intentionall
y Left Blank
409 Space Allocation 
Code
Coded indication of the action 
requested, taken or confirmed 
related to space allocation
aa SS 1.7
Sub Element ID Format Description
409D001 aa Space Allocation Code
410 Accounting 
Information Detail of accounting information t[...34]
PAYMENT BY 
CERTIFIED 
CHEQUE
Sub Element ID Format Description
410D001 t[...34] Accounting Information
411
Accounting 
Information 
Identifier
Code indicating a specific kind 
of accounting information
aaa GBL 1.30
Sub Element ID Format Description
411D001 aaa Accounting Information Identifier
412 Handling Detail Description of handling 
information
t[...38] KEEP UPRIGHT
Sub Element ID Format Description
412D001 t[...38] Handling Detail
413 Handling Detail 
Identifier
Code indicating a specific kind 
of handling detail
aaa SPH 1.29
Sub Element ID Format Description
413D001 aaa Handling Detail Identifier (SPH)
413D002 aaa Handling Detail Identifier (SSR)
413D003 aaa Handling Detail Identifier (NFY)
414 Signature Name of signatory t[...20] K. WILSON
Sub Element ID Format Description
414D001 t[...20] Signature
415 Amendment 
Details
Information relating to 
amendments
t[...65] TEXT Can include slant (/) within 
text.
Sub Element ID Format Description
415D001 t[...65] Amendment Details
416
Domestic/Inter
national 
Indicator
Coded indicator specifying the 
ultimate transit status of a 
bonded movement (domestic or 
international)
a D 1.37
417 Allotment 
Identification
Reference assigned to 
Guaranteed Capacity on one or 
more specific flights on specific 
date(s) to third parties such as 
Agents and Other Airlines
m[1...14] MRC7615164 Capacity with respect to 
Weight, Volume and ULDs.
Sub Element ID Format Description
417D001 m[1..14] Allotment Identification
418
Reason for 
Acknowledgeme
nt
Reason for 
Rejection/Err
or
The reason for the transmission 
of either a Message 
Acknowledgement (FMA) 
Message or an Error (FNA) 
Message
t[...65]
Sub Element ID Format Description
418D001 t[...65] Reason for Acknowledgement

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
418D002 t[...65] Reason for Rejection/Error
419
Connection 
Restriction 
Indicator
Code indicating the restrictions 
applying to combination of 
flights
a N 1.42
Sub Element ID Format Description
419D001 a Connection Restriction Indicator
420 Reason for No 
Display
Explanation why a positive 
answer has not been given
t[...65]
NO FLIGHT 
OPERATING 
THAT DAY
Sub Element ID Format Description
420D001 t[...65] Reason for No Display
421 Allotment 
Status Code
Code indicating the status for a 
nominated allotment
a O 1.87
Sub Element ID Format Description
421D001 a Allotment Status Code
422 Delivery/Pickup 
Indicator
Code indicating whether a 
vehicle is delivering or picking 
up consignments at a terminal 
loading dock
a P
Sub Element ID Format Description
422D001 a Deliver/Pickup Indicator
423 Loading Order 
Indicator
Code indicating that the 
sequence of consignment 
details within a message is the 
order consignments are to be 
loaded
a Y
Sub Element ID Format Description
423D001 a Loading Order Indicator
424 Customs Duty 
Indicator
Code identifying whether 
customs duty is payble or not 
on a courier baggage voucher 
shipment
a Y
Sub Element ID Format Description
424D001 a Customs Duty Indicator
500 Volume Amount Cubic measure of a 
consignment
n[...9]p 12.92 Element values limited to 
range 0.01–999999999
Sub Element ID Format Description
500D001 n[...9]p Volume Amount
501 Charge Amount Discount 
Amount An amount of money n[...12]p 120.46 Element values limited to 
range 0.000–999999999999
Sub Element ID Format Description
501D001 n[...12]p Charge Amount
501D002 n[...12]p Charge Amount (Sub-Total)
501D003 n[...12]p Charge Amount (Weight)
501D004 n[...12]p Charge Amount (Valuation)
501D005 n[...12]p Charge Amount (Total)
501D006 n[...12]p Discount Amount
501D007 n[...12]p Charge Amount (CASS)
502 Charge 
Identifier
Code identifying a charge sub-
total or total
aa VC 1.33
Sub Element ID Format Description
502D001 aa Charge Identifier (CT)
502D002 aa Charge Identifier (WT)

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
502D003 aa Charge Identifier (VC)
502D004 aa Charge Identifier (TX)
502D005 aa Charge Identifier (OA)
502D006 aa Charge Identifier (OC)
503 Charge Code Code identifying a method of 
payment of charges aa CC 1.1
Sub Element ID Format Description
503D001 aa Charge Code
504 Other Charge 
Code
Code identifying the type of an 
individual charge
aa AC 1.2
Sub Element ID Format Description
504D001 aa Other Charge Code
505 Service Code Code to identify cargo products a D 1.38
Sub Element ID Format Description
505D001 a Service Code
506 Rate or Charge Discount Representation of a rate, charge 
or discount
n[...8]p 1234.56
Element values limited to 
range 0.0001–
99999999May be increased 
to 9 characters in the 
future.
Sub Element ID Format Description
506D001 n[...8]p Rate or Charge
506D002 n[...8]p Discount
507 Rate Class Code Code representing a specific 
rate category
a M 1.4
Sub Element ID Format Description
507D001 a Rate Class Code
507D002 a Rate Class Code (Basic)
508 Amount of 
Insurance
No Value 
(XXX)
The value of a shipment for 
insurance purposes
n[...11]p 
or XXX 1000.00 1.31 Element values limited to 
range 0.001–99999999999
Sub Element ID Format Description
508D001 n[...11]p Amount of Insurance
508D002 aaa No Value (XXX)
509 Declared Value 
for Customs
No Customs 
Value (NCV)
The value of a shipment for 
Customs purposes
n[...12]p 
or NCV 120.00 1.31 Element values limited to 
range 0.001–999999999999
Sub Element ID Format Description
509D001 n[...12]p Declared Value for Customs
509D002 aaa No Customs Value (NCV)
510 Declared Value 
for Carriage
No Value 
Declared 
(NVD)
The value of a shipment 
declared for carriage purposes
n[...12]p 
or NVD 100.00 1.31 Element values limited to 
range 0.001–999999999999
Sub Element ID Format Description
510D001 n[...12]p Declared Value for Carriage
510D002 aaa No Value Declared (NVD)
511 Class Rate 
Percentage
A surcharge or discount 
percentage applied to an 
applicable rate or charge
n[...3] 67
Sub Element ID Format Description
511D001 n[...3] Class Rate Percentage
512 —
Intentionall
y Left Blank

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
512D001 (a)nnn Surcharge Percentage
513 ULD Rate Class 
Type
Coded description of a Unit 
Load Device rate class n(a)(a) 8 See CTCC Resolutions 
Manual, Resolution 523.
Sub Element ID Format Description
513D001 n(a)(a) ULD Rate Class Type
514 Discount Discount amount applied under 
specified conditions
n[...8]p 24.30 Element values limited to 
range 0.001–99999999
Sub Element ID Format Description
514D001 n[...8]p Discount (ULD)
515 Rate Type Code Code indicating a specific type 
of rate(s)
aaa SCR 1.43
Sub Element ID Format Description
515D001 aaa Rate Type Code
516 ULD Charge 
Code
Code explaining the nature of a 
ULD rate/charge
a A 1.44
Sub Element ID Format Description
516D001 a ULD Charge Code
517 Rate Note Reference referring to a specific 
rate/charge rule
mmmm S095
Sub Element ID Format Description
517D001 mmmm Rate Note
518
Rate 
Information 
Type
Code indicating a specific type 
of rate information
a C 1.45
Sub Element ID Format Description
518D001 a Rate Information Type
519 Credit Amount 
Indicator
An indication that an amount is 
a credit aa CR 1.78
Sub Element ID Format Description
519D001 aa Credit Amount Indicator
520
Tax 
Identification 
Code
Coded value for particular types 
of taxes
aa VA 1.79
Sub Element ID Format Description
520D001 aa Tax Identification Code
521 Surface Charge 
Identifier
Code identifying a surface 
charge sub-total or total
aa CM 1.89
Sub Element ID Format Description
521D001 aa Surface Charge Identifier
600 Weight Weight measure n[...7]p 140.5 Element values limited to 
range 0.1–9999999
Sub Element ID Format Description
600D001 n[...7]p Weight
600D002 n[...7]p Weight (CASS)
601 Weight Code Code identifying a unit of 
weight
a K 1.24
Sub Element ID Format Description
601D001 a Weight Code
602 Density Group Code indicating approximate 
density of goods
n[...2] 9 2
Sub Element ID Format Description
602D001 n[...2] Density Group
603 Density 
Indicator Code indicating density group aa DG 1.23

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
603D001 aa Density Indicator
604 Volume Code Code indicating unit of volume aa CF 1.22
Sub Element ID Format Description
604D001 aa Volume Code
605 —
Intentionall
y Left Blank
Sub Element ID Format Description
605D001 aaa IATA Currency Code
606 ISO Currency 
Code
Coded representation of a 
currency approved by ISO aaa GBP See IATA Airline Coding 
Directory.
Sub Element ID Format Description
606D001 aaa ISO Currency Code
607 Rate of 
Exchange
Currency 
Conversion 
Rate
The rate at which one specified 
currency is expressed in another 
specified currency
n[...11]p 2.15000 Values limited to range 
0.000001–99999999999
Sub Element ID Format Description
607D001 n[...11]p Rate of Exchange
608 Length 
Dimension Length of pieces n[...5] 200
Sub Element ID Format Description
608D001 n[...5] Length Dimension
609 Width 
Dimension Width of pieces n[...5] 150
Sub Element ID Format Description
609D001 n[...5] Width Dimension
610 Height 
Dimension Height of pieces n[...5] 100
Sub Element ID Format Description
610D001 n[...5] Height Dimension
611 Measurement 
Unit Code
Indication of the unit of 
measurement in which 
measurements are expressed
m[...3] CMT 1.48
Sub Element ID Format Description
611D001 m[...3] Measurement Unit Code
612
CASS 
Commission 
Code
Code indicating the commission 
percentages agreed by each 
airline
ann A26
Sub Element ID Format Description
612D001 ann CASS Commission Code
613
CASS 
Settlement 
Factor
Special rate or charge agreed 
bilaterally between an airline 
and a cargo agent for individual 
transactions
n[...12]p 139
Sub Element ID Format Description
613D001 n[...12]p CASS Settlement Factor
614 CASS Indicator Indicator used in CASS 
messages
a[...2] N 1.80
This switch indicates 
whether commission or 
sales incentive applies, 
whether an AWB is used as 
an invoice or service, 
cancelled or voided, 
whether a tax calculation is 
required, whether an 
amount is original or 
revised and late reporting 
waybills.

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
614D001 a[...2] CASS Indicator
615 CASS Billing 
Period
CASS 
Reporting 
Period
Identification of the CASS billing 
period nnn 001
Sub Element ID Format Description
615D001 nnn CASS Billing Period
615D002 nnn CASS Reporting Period
700 Number (of 
AWBs) Number of AWBs n[...4] 12
701 Number of 
Pieces
Number of Loose Items and/or 
ULD’s as accepted for carriage
Format: n
[...4] 8
Sub Element ID Format Description
701D001 n[...4] Number of Pieces
701D002 n[...4] Number of Pieces (Landed)
701D003 n[...4] Number of Pieces (Total)
701D004 n[...4] Number of Pieces (This Dimension)
701D005 n[...4] Number of Pieces (Manifested)
701D006 n[...4] Number of Pieces (Actioned)
702 Number of ULDs Number of Unit Load Devices 
(Aircraft Pallets or Containers)
n[...2] 4
Sub Element ID Format Description
702D001 n[...2] Number of ULDs (Total)
702D002 n[...2] Number of ULDs (This Type)
703
Shipment 
Description 
Code
Code indicating whether a 
shipment is a total, part or split 
consignment
a P 1.15
Sub Element ID Format Description
703D001 a Shipment Description Code (T or P)
703D002 a Shipment Description Code (T)
703D003 a Shipment Description Code
704 Movement 
Priority Code
Code indicating a specific 
priority for carriage
a H 1.12
Sub Element ID Format Description
704D001 a Movement Priority Code
705 Special 
Handling Code
Dangerous 
Goods Code 
(subset of 
Special 
Handling 
Code)
Code indicating that nature of 
consignment may necessitate 
use of special handling 
procedures
aaa EAT 1.14
Sub Element ID Format Description
705D001 aaa Special Handling Code (1)
705D002 aaa Special Handling Code (2)
706 Discrepancy 
Code
Code indicating a specific 
discrepancy
aaaa FDCA 1.8
Sub Element ID Format Description
706D001 aaaa Discrepancy Code
707 Commodity 
Item Number
Number to identify a specific 
commodity
n[4...7] 9017 See CTCC Resolutions 
Manual, Resolution 590aa.
Sub Element ID Format Description
707D001 n[4...7] Commodity Item Number

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
708
Manifest 
Description of 
Goods
Description of the goods for 
manifest purposes t[..15] TELEVISION 
SETS
Sub Element ID Format Description
708D001 t[...15] Manifest Description of Goods
709
Nature and 
Quantity of 
Goods
Description 
for 
Dangerous 
Goods
Description of the goods t[...20] TOOTH PASTE
For Description for 
Dangerous Goods, see IATA 
Dangerous Goods 
Regulations.
Sub Element ID Format Description
709D001 t[...20] Nature and Quantity of Goods
709D002 t[...20] Description for Dangerous Goods
710 Goods Data 
Identifier
Code indicating a particular 
nature and quantity of goods
a G 1.28
Sub Element ID Format Description
710D001 a Goods Data Identifier
711 Part Arrival 
Reference
Code indicating that a specific 
part of a split shipment has 
arrived
a A
712 Quantity 
Identifier
Code identifying a particular 
quantity
a B 1.27
713
Supplementary 
Rate 
Information
Explanation of rate information 
given
t[...65]
COMBINATION 
WITH OTHER 
CARGO RATES 
PROHIBITED
Sub Element ID Format Description
713D001 t[...65] Supplementary Rate Information
714 SLAC Shipper’s Load and Count n[...5] 15000
Sub Element ID Format Description
714D001 n[...5] SLAC
715
DG Class or 
Division Number 
and 
Compatability 
Group
Class or division number and 
compatability group associated 
with a dangerous goods item
t[...4] 6.1 See IATA Dangerous Goods 
Regulations.
Sub Element ID Format Description
715D001 t[...4] DG Class or Division Number and Compatibility Group
716 DG UN or ID 
Prefix
Code to indicate the entity 
numbering a dangerous goods 
item
aa UN 1.82
Sub Element ID Format Description
716D001 aa DG UN or ID Prefix
717 DG UN or ID 
Number
Number identifying a dangerous 
goods item
n[4] 2165 See IATA Dangerous Goods 
Regulations.
Sub Element ID Format Description
717D001 n[4] DG UN or ID Number
718 DG Subsidiary 
Risk
Number identifying the 
subsidiary risk of a dangerous 
goods item
n[...3]p 6.1 See IATA Dangerous Goods 
Regulations.
Sub Element ID Format Description
718D001 n[...3]p DG Subsidiary Risk
719 Overpack 
Indicator
Code idicating that an overpack 
was used for packaging of a 
dangerous goods item
a O 1.83
Sub Element ID Format Description
719D001 a Overpack Indicator
720 Quantity Numeric indication of a quantity n[...7]p 0.2
Sub Element ID Format Description

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
720D001 n[...7]p Quantity
721
DG UN 
Packaging 
Specification 
Code
Code indicating the UN 
packaging specification of a 
dangerous goods item
m[...4] 1A1 See IATA Dangerous Goods 
Regulations.
Sub Element ID Format Description
721D001 m[...4] DG UN Packaging Specification Code
722 DG Q Value Quantity value of a dangerous 
goods Item
n[...3]p 0.9
Sub Element ID Format Description
722D001 n[...3]p DG Q Value
723 Overpack 
reference
Reference of the overpack 
packaging of a dangerous goods 
item
m[10] A123
Sub Element ID Format Description
723D001 m[...10] Overpack Reference
724 Radioactive 
Activity
Numeric expression of the 
activity of a radioactive Item
n[...8]p 1925
Sub Element ID Format Description
724D001 n[...8]p Radioactive Activity
725
DG Packing 
Instruction 
Number
Code indicating the packing 
instruction of a dangerous 
goods item
(a)nnn Y305 See IATA Dangerous Goods 
Regulations.
Sub Element ID Format Description
725D001 (a)nnn DG Packing Instruction Number
726 DG Packing 
Group
Code indicating the packing 
group of a dangerous goods 
item
a[...3] III See IATA Dangerous Goods 
Regulations.
Sub Element ID Format Description
726D001 a[...3] DG Packing Group
727 Category 
Number
Group 
Number
Code indicating the radioactive 
category or LSA/SCO group of a 
radioactive item
a[...3] III See IATA Dangerous Goods 
Regulations.
Sub Element ID Format Description
727D001 a[...3] Category Number
727D002 a[...3] Group Number
728 Category Color
Code indicating the radioactive 
category color of a radioactive 
item
a Y 1.84
Sub Element ID Format Description
728D001 a Category Color
729 Radioactive 
Transport Index
Numeric indication of the 
transport index of a radioactive 
item
n[...3]p 0.3
Sub Element ID Format Description
729D001 n[...3]p Radioactive Transport Index
730 Fissile Excepted 
Indicator
Code indicating a fissile 
excepted radioactve item
a Y 1.85
Sub Element ID Format Description
730D001 a Fissile Excepted Indicator
731 LSA/SCO 
Indication
Indication that a radioactive 
item has low specific activity or 
that a solid object is a surface 
contaminated object 
(radioactive material distributed 
on its surface)
aaa LSA
Sub Element ID Format Description

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
731D001 aaa LSA/SCO Indication
732 Criticality Safety 
Index
An indication that of the critical 
safety index for radioactive 
material
n[...4]p 2.0 Values limited to range 0.1–
50.0
Sub Element ID Format Description
732D001 n[...4]p Criticality Safety Index
733 Quantity 
Indicator
An indication that a quantity is 
either net or gross a N 1.101
Sub Element ID Format Description
733D001 a Quantity Indicator
800 Flight Number
Substitute 
Flight 
Number
Number to identify a flight or a 
substitute flight
nnn(n)(a) 514, 0514, 
0514A, 514A
The trailing alpha (a) 
character is in fact an 
operational suffix and not 
part of the actual flight 
number.
Sub Element ID Format Description
800D001 nnn(n)(a) Flight Number
801 ULD Owner 
Code
Code to identify the owner of a 
Unit Load Device
mm TW
Actual format is “aa”, “an” 
or “na”.Owner can be an 
airline or leasing 
company.See IATA ULD 
Technical Manual.
Sub Element ID Format Description
801D001 mm ULD Owner Code
802 ULD Type Code identifying a standard Unit 
Load Device type amm ASE See IATA ULD Technical 
Manual.
Sub Element ID Format Description
802D001 amm ULD Type
803 ULD Volume 
Available Code
Code indicating the proportion 
of the volume in a Unit Load 
Device which remains unfilled
n 1 1.20
Sub Element ID Format Description
803D001 n ULD Volume Available Code
804 ULD Remarks Information related to a specific 
Unit Load Device
t[...53] ULD PREPARED 
BY DANZAS
Sub Element ID Format Description
804D001 t[...53] ULD Remarks
805
ULD Control 
Receipt Serial 
Number
A reference number used to 
identify a particular Unit Load 
Device Control Receipt within an 
airline
n[8] 12345675
806 ULD Condition 
Code
Code describing the physical 
condition of a Unit Load Device
aaa SER 1.21
807 Main Deck Only 
Indicator
Code identifying that a Unit 
Load Device is restricted to 
main deck loading position
a M 1.6
Sub Element ID Format Description
807D001 a Main Deck Only Indicator
808 Aircraft 
Registration
Identification of Aircraft, aircraft 
markings of Nationality and 
Registration
t[...10] PHBUB
Sub Element ID Format Description
808D001 t[...10] Aircraft Registration
809 Aircraft 
Possibility Code
Code indicating the 
transportation possibilities of an 
aircraft
aaa BBQ 1.46
Sub Element ID Format Description

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
809D001 aaa Aircraft Possibility Code
810 Aircraft Type 
Code
Code identifying a specific type 
of aircraft mmm 74M See IATA Airline Coding 
Directory.
Sub Element ID Format Description
810D001 mmm Aircraft Type Code
811 ULD Loading 
Indicator
Code indicating ULD height or 
loading limitation
a L 1.47
Sub Element ID Format Description
811D001 a ULD Loading Indicator
812 Vehicle Type Identification of a particular 
type of vehicle
t[...15] FLATBED
Sub Element ID Format Description
812D001 t[...15] Vehicle Type
813 Route Label Truck route identification nnn(n) 999
Sub Element ID Format Description
813D001 nnn(n) Route Label
814
Supplemental 
Truck/Route 
Indicator
Coded supplemental truck or 
routing information
a P
Sub Element ID Format Description
814D001 a Supplemental Truck/Route Indicator
815 Movement 
Indicator
Code indicating the type of 
movement for a means of 
transport, e.g. departure, 
arrival, delay
mm AD 1.92
Sub Element ID Format Description
815D001 mm Movement Indicator
816 Delay Reason 
Codes
Code indicating the reason for a 
delay in the movement of a 
means of transport
mm 41
See IATA Airport Handling 
Manual. The actual format 
used can only be two alpha 
codes (aa) or two numeric 
codes (nn). For the purpose 
of the Surface 
Transportation Movement 
(STM) Message the means 
of transportation is “TRUCK” 
truck rather than 
“AIRCRAFT”.
Sub Element ID Format Description
816D001 mm Delay Reason Codes
817 ULD Contour 
Code
Code indicating the exact 
contour of a ULD including its 
footprint
mm(m) S7 1.98
Sub Element ID Format Description
817D001 mm(m) ULD Contour Code
900
Harmonised 
Commodity 
Code
Number identifying goods for 
Customs or statistical purposes
m[6...18] 427127829
Sub Element ID Format Description
900D001 m[6...18] Harmonized Commodity Code
901
Customs 
Amendment 
Code
Code indicating the reason for 
transmitting an amendment to 
Customs
nn 69 Codes defined locally by 
customs.
Sub Element ID Format Description
901D001 nn Customs Amendment Code
902 Customs 
Notification
Information provided to, or 
received from, Customs
t[...20] TYPING ERROR

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
902D001 t[...20] Customs Notification
903 Customs Status 
Code
Coded representation of the 
current status of a shipment 
actioned by Customs
aa CC Codes defined locally by 
customs.
Sub Element ID Format Description
903D001 aa Customs Status Code
904 Customs Entry 
Number
Number assigned to the 
Customs Entry by Customs
m[...35] 48622
Sub Element ID Format Description
904D001 m[...35] Customs Entry Number
905
Customs 
Clearance Split 
Number
Number assigned to a specific 
portion of a consignment for 
clearance purposes
nn 01
906 Customs Origin 
Code
Code indicating the origin of 
goods for Customs purposes
m[...2] T2 1.49 List to be provided by local 
customs authorities.
Sub Element ID Format Description
906D001 m[...2] Customs Origin Code
907 Customs 
Reference
A reference used by Customs to 
identify a shipment t[...15] JFK42176
Sub Element ID Format Description
907D001 t[...15] Customs Reference
908 Customs Action 
Code
Coded representation of a 
specific Customs action
nnn 001 Codes defined locally by 
customs.
Sub Element ID Format Description
908D001 nnn Customs Action Code
909 CCS Group Code
Code identifying the type of 
participant involved in a cargo 
community system
mmm CNE 1.63
910 CCS Participant 
Identifier
Coded identification of a 
participant involved in a cargo 
community system
m[...21] JMC List of codes maintained by 
each CCS.
911 CCS System 
Identifier
Code identifying a cargo 
community system or a Value 
Added Network (VAN)
mmm CCH 1.60
912 CCS Code Type
Code indicating a specific type 
of address structure used in 
cargo community systems for 
participant identification
mm 01 1.61
913 CCS Participant 
Office
Code identifying the office or 
terminal of a cargo community 
system participant
n[...2] 1 List of codes maintained by 
each CCS.
914 CCS ID Code 
Qualifier
Code identifying the participant 
identification format used in a 
cargo community system
m[...4] Z1 1.62
915 CCS Reverse 
Routing Address
CCS Routing 
Address
Information to identify a 
computer sub-address
m[...14] 256
921
Mail 
Consignment 
Number
Number allocated by a postal 
administration to an air mail 
consignment
m[...10] 123456789
Sub Element ID Format Description
921D001 m[...10] Mail Consignment Number
922 Mail Category 
Code
Code indicating a category of 
mail
m A 1.70
Sub Element ID Format Description
922D001 m Mail Category Code
923 Mail Class Code Code indicating a class of mail m U 1.71
Sub Element ID Format Description

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
924D001 m Mail Class Code
924 Mail ULD Type 
Code
Code indicating a type of mail 
ULD mmmm 11 1.75 List of codes to be provided 
by UPU.
Sub Element ID Format Description
924D002 mmmm Mail ULD Type Code
925 Mail ULD Seal 
Number
Security Seal 
Number
Seal number allocated by a 
postal administration to a mail 
ULD or a seal number allocated 
to a ULD
m[...10] 123456789
Sub Element ID Format Description
925D001 m[...10] Mail ULD Seal Number
925D002 m[...10] Security Seal Number
926 Despatch Serial 
Number
Serial number allocated by a 
postal administration to a 
despatch
n[...4] 1234
Sub Element ID Format Description
926D001 n[...4] Despatch Serial Number
927 Mail Sub-Class 
Code Code indicating a mail sub-class mm UN 1.76 List of codes to be provided 
by UPU.
Sub Element ID Format Description
927D001 mm Mail Sub-Class Code
928 Receptacle Type 
Code
Code indicating a receptacle 
type
mm BG 1.72
Sub Element ID Format Description
928D001 mm Receptacle Type Code
929 Receptacle 
Number
Bar Code 
Content
Number allocated by a postal 
administration to a receptacle
m[...35] 123456789
Sub Element ID Format Description
929D001 m[...35] Receptacle Number
929D002 m[...35] Bar Code Content
930 Mail Dangerous 
Goods Indicator
Indicator showing that a mail 
consignment contains 
dangerous goods
a Y 1.73
Sub Element ID Format Description
930D001 a Mail Dangerous Goods Indicator
931 Mail Handling 
Class Code
Code indicating a mail handling 
class
a N 1.74
Sub Element ID Format Description
931D001 a Mail Handling Class Code
932 Number of 
Receptacles Number of receptacles n[...5] 10
Sub Element ID Format Description
932D001 n[...5] Number of Receptacles
933 EDIFACT 
Location Code
Code indicating an EDIFACT 
location
a[5] FRPAR List of codes published by 
UN/ECE.
Sub Element ID Format Description
933D001 a[5] EDIFACT Location Code
934 Bar Code Type Code indicating the bar code 
type
a R 1.93
Sub Element ID Format Description
934D001 a Bar Code Type
935 Expected 
Indicator
Code indicating whether the 
receptable is to be received or 
not at the station that is 
receiving the message
a Y 1.94

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
Sub Element ID Format Description
935D001 a Expected Indicator
936 Mail Status 
Event Code
Coded representation of the 
current status of a mail 
consignment
aaa HND 1.95
Sub Element ID Format Description
936D001 aaa Mail Status Event Code
937 Mail Status 
Reason Code
Coded representation of the 
reason for the current status of 
a mail consignment
m[...3] 63 List of codes published by 
UN/ECE
Sub Element ID Format Description
937D001 m[...3] Mail Status Reason Code
938 Mail Mode Code indicating the mode of the 
inbound/outbound mail
a H 1.96
Sub Element ID Format Description
938D001 a Mail Mode
939 Mail Mode 
Description
Description related to the 
inbound/outbound mail mode
t[...12]
Sub Element ID Format Description
939D001 t[...12] Mail Mode Description
940
Supplementary 
Customs, 
Security and 
Regulatory 
Control  
Information
Supplementary information 
identifying a party or a location 
related to Customs, Security 
and Regulatory Control 
reporting requirements
t[...35] BCBP123
Sub Element ID Format Description
940D001 t[...35] Supplementary Customs, Security and Regulatory Control Information
941
Customs, 
Security and 
Regulatory 
Control 
Information 
Identifier
Coded indicator qualifying 
Customs, Security and 
Regulatory Control related 
information
a[...2] A 1.100
Sub Element ID Format Description
941D001 a[...2] Customs, Security and Regulatory Control Information Identifier
942 Screening 
Method
An indication of the screening 
method used to ensure the 
security of a consignment
aaa EDS 1.102
Sub Element ID Format Description
942D001 aaa Screening Method
943 Screening 
Status
An indication of the security 
status assigned to a 
consignment
aaa SPX 1.103
Sub Element ID Format Description
943D001 aaa Screening Status
944 Screening 
Exemption
An indication of the grounds for 
granting an exemption from 
security screening to a 
consignment
aaaa DIPL 1.104
Sub Element ID Format Description
944D001 aaa Screening Exemption
945 Mail Handling 
Unit Type
An indication of the type of unit 
(not a ULD) being used during 
mail handling operations.
a
Sub Element ID Format Description
945D001 a Mail Handling Unit Type

ev ImagData Element No Name Alternate Name Description Format Example Reference Note
946 Mail Handling 
Unit Identifier
The identifier affixed to a unit 
(not a ULD) being used during 
mail handling operations.
t[...15]
Sub Element ID Format Description
946D001 t[...15] Mail Handling Unit Identifier

Code List Grid

Rev Image Ref No Abbr Name Type Data Element Notes
1.1 Charge Codes general 503
Meaning Abbr Code Notes
Context:
All Charges Collect CC
All Charges Collect by Credit Card CZ
All Charges Collect by GBL CG
All Charges Prepaid Cash PP
All Charges Prepaid Credit PX
All Charges Prepaid by Credit Card PZ
All Charges Prepaid by GBL PG
Destination Collect Cash CP
Destination Collect Credit CX
Destination Collect by MCO CM
No Charge NC
No Weight Charge — Other Charges Collect NT
No Weight Charge — Other Ch arges Prepaid by Credit Card NZ
No Weight Charge — Other Charges Prepaid by GBL NG
No Weight Charge — Other Charges Prepaid Cash NP
No Weight Charge — Other Charges Prepaid Credit NX
Partial Collect Credit — Partial Prepaid Cash CA
Partial Collect Credit — Partial Prepaid Credit CB
Partial Collect Credit Card — Partial Prepaid Cash CE
Partial Collect Credit Card — Partial Prepaid Credit CH
Partial Prepaid Cash — Partial Collect Cash PC
Partial Prepaid Credit — Partial Collect Cash PD
Partial Prepaid Credit Card — Partial Collect Cash PE
Partial Prepaid Credit Card — Partial Collect Credit PH
Partial Prepaid Credit Card — Partial Collect Credit Card PF
1.2 Other Charge Codes general 504
Meaning Abbr Code Notes
Context:
Adjusting of improperly loaded ULD UC
Advances and/or guarantees BA
Airport arrival FA
Appraisal Service BB
AWB Cancellation DG
AWB Charges Correction Advice DH
AWB Copy BC
Air Waybill Fee AW
AWB Re-waybilling DI
Animal Container AC
Assembly Service Fee AS
Attendant AT
Bank Release BR
Blacklist Certificate BL
Bonding CA

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Certificate of Origin DC
Charges Collect Fee FC
Cleaning LC
Cleaning of stalls/pens LI
Clearance and Handling — Destination CD
Clearance and Handling — Origin CH
Clearance, General JA
Collection of funds BE
Completion/preparation of documents CB
Cool/Cold room, freezer (Perishables) PB
Cool/Cold room, freezer (Storage) ZC
Copies of documents BF
Dangerous Goods Fee RA
Delivery SA
Delivery notification SB
Delivery Order SF
Demurrage UD
Diplomatic consignment GA
Disassembly UB
Disbursement Fee DB
Distribution Service Fee DF
Domestic shipments FB
Electronic processing or transmission of data for customs purposes
CG
Export/Import warrant CE
Fuel Surcharge — Due Issuing Carrier MY
General (Handling) FE
General (Storage) ZB
General Taxes TX
Government Tax GT
Handling (Express) EA
Handling (Heavy/Bulky cargo) KA
Handling (Perishables) PA
Handling (Unit Load Device) UH
Handling (Valuable Cargo) VA
Handling (Vulnerable cargo) WA
Hotel LE
Human Remains HR
Import/export documents processing BI
Inventory and/or inspection CF
Insurance Premium IN
Leasing UE
Loading/unloading FF
Loading/unloading equipment (forklift etc.) KB

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Live Animals LA
Manual data entry for customs purposes CC
Messenger service BH
          Miscellaneous — Due Agent (see Note 1) MA
MA code is used if the miscellaneous charge is due agent but cannot 
be further identified.
          Miscellaneous — Due Carrier (see Note 3) MC
MC code is used if the miscellaneous charge is due carrier but cannot 
be further identified.
Miscellaneous — Due Issuing Carrier MO to MX
Miscellaneous — Due Issuing Carrier MZ
Miscellaneous — Due Last Carrier MD to MN
          Miscellaneous — Unassigned (see Note 2) MB
MB code is used if the miscellaneous charge cannot be determined as 
being due agent or due carrier.
Mortuary HB
Navigation Surcharge — Due Issuing Carrier NS
Overtime and Other Customs Imposed Charges CI
Packing/Repacking PK
Pick-Up PU
Postal Tax TA
Preparation of Cargo manifest DD
Priority FD
Proof of delivery (documentation) DJ
Proof of delivery (pickup and delivery) SE
Quarantine LF
Radio-active room RD
Recontouring UF
Referral of Charge RC
Rejection RB
Release order DK
Remit Following Collection Fee RF
Removal (carrier warehouse to warehouse) CJ
Rental of Stalls/pens LJ
Re-warehousing ZA
Sales Tax TB
Security (armed guard/escort) handling VB
Security Charge SC
Security (Surcharge/premiums) XB
Separate Early Release SP
Signature Service SS
Stamp Tax TC
State Sales Tax ST
State Tax TD
Statistical Tax TE
Stop in Transit SI
Storage — Destination SR

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Storage (Live animals) LH
Storage — Origin SO
Strongroom VC
Surface Charge — Destination SD
Surface Charge — Origin SU
Time XC
Transit TR
Unloading (Unit Load Device) UG
Value Added Tax (General or for Export) TV
Value Added Tax (For Import only) TI
Very important cargo (VIC) IA
Veterinary and/or Phytosanitary purposes DV
Veterinary inspection LG
War risk XD
Weighing FI
Weight XE
Withdrawal of shipment after clearance BM
1.3 Entitlement Codes general 315
Meaning Abbr Code Notes
Context:
Other Charges due Agent A
Other Charges due Carrier C
1.4 Rate Class Codes general 507
Meaning Abbr Code Notes
Context:
Basic Charge B
Class Rate Reduction R
Class Rate Surcharge S
International Priority Service Rate P
Minimum Charge M
Normal Rate N
Quantity Rate Q
Rate per Kilogram K
Specific Commodity Rate C
Unit Load Device Additional Information X
Unit Load Device Additional Rate E
Unit Load Device Basic Charge or Rate U
Unit Load Device Discount Y
1.5 Prepaid/Collect Indicators general 403
Meaning Abbr Code Notes
Context:
Collect Indicator C
Prepaid Indicator P
1.6 Main Deck Only Indicator general 807
Meaning Abbr Code Notes
Context:

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Main Deck Only Indicator M
1.7 Space Allocation Codes general 409
Meaning Abbr Code Notes
Context: Action Codes
Cancel Any Previous Space Allocation XX
Reporting Sale SS
Requesting Space Allocation, if Not Available Will Accept 
Alternative NA
Requesting Space Allocation, for Wait List NL
Requesting Space Allocation, Will Not Accept Alternative NN
Selling Space Allocation Against Allotment CA
Context: Advice Codes
Cancellation Noted CN
Confirming KK
Unable UU
Unable, Flight Does Not Operate UN
Wait List LL
Context: Status Codes
Have Requested Space Allocation HN
Holding Confirmed HK
Holding Wait List HL
1.8 Discrepancy Codes general 706 Refer to Recommended Practice 1600q.
Meaning Abbr Code Notes
Context: Cargo
Found Air Waybill FDAW
Found Cargo FDCA
Missing Air Waybill MSAW
Missing Cargo MSCA
Context: Mail
Found Mail Document FDAV
Found Mailbag FDMB
Missing Mail Document MSAV
Missing Mailbag MSMB
Context: Miscellaneous
Definitely Loaded DFLD
Offloaded OFLD
Overcarried OVCD
Shortshipped SSPD
1.9 End of Message Codes general 102
Meaning Abbr Code Notes
Context:
End of Total Message LAST
End of Part Message CONT
1.10 Change Codes general 401
Meaning Abbr Code Notes
Context:
Add AD
Change CH

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Delete DL
1.11 Months general 201
Meaning Abbr Code Notes
Context:
January JAN
February FEB
March MAR
April APR
May MAY
June JUN
July JUL
August AUG
September SEP
October OCT
November NOV
December DEC
1.12 Movement Priority Codes general 704
Meaning Abbr Code Notes
Context:
Consignment Under Bond B
Express Parcel Shipment E
Express Shipments X
High Priority H
Low Priority L
Service Shipment S
1.13 Nil Cargo Code general 402
Meaning Abbr Code Notes
Context:
No Cargo NIL
1.14 Dangerous Goods Codes general 705
Meaning Abbr Code Notes
Context:
Cargo Aircraft Only CAO
Lithium Ion Batteries otherwise excepted from the IATA DGR ELI
Lithium Metal Batteries otherwise excepted from the IATA DGR ELM
Corrosive RCM
Cryogenic Liquids RCL
Dangerous When Wet RFW
Dry Ice ICE
To be reserved for normally forbidden Explosives, Divisions 1.1, 
1.2, 1.3, 1.4F, 1.5 and 1.6 REX
Explosives 1.3C RCX
Explosives 1.3G RGX
Fully Regulated Lithium Ion Batteries (Class 9) RLI
Fully Regulated Lithium Metal Batteries (Class 9) RLM
Explosives 1.4B RXB

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Explosives 1.4C RXC
Explosives 1.4D RXD
Explosives 1.4E RXE
Explosives 1.4G RXG
Explosives 1.4S RXS
Flammable Gas RFG
Flammable Liquid RFL
Flammable Solid RFS
Infectious Substance RIS
Magnetized Material MAG
Miscellaneous Dangerous Goods RMD
Non-Flammable Non-Toxic Gas RNG
Organic Peroxide ROP
Oxidizer ROX
Toxic Substance RPB
Toxic Gas RPG
Polymeric Beads RSB
Radioactive Material Category I-White RRW
Radioactive Material Categories II-Yellow and III-Yellow RRY
Spontaneously Combustible RSC
1.15 Shipment Description Codes general 703
For the purpose of these Codes:
Total Consignment = total number of pieces of 
complete shipment.
 Part Consignment = those pieces less than the 
total consignment carried on one flight.
 Split Consignment = those pieces of a total 
consignment carried in more than one ULD(s) 
and/or bulk on the same flight.
 Divided Consignment = those pieces of a part 
consignment in more than one ULD(s) and/or 
bulk on the same flight.
 Multi-Shipments = those pieces less than the 
total consignment carried on more than one 
flight.
Meaning Abbr Code Notes
Context:
Divided Consignment D
Multi-Shipments M
Part Consignment P
Split Consignment S
Total Consignment T
1.16 Special Handling Codes general 705
          Dangerous Goods codes described in 1.14 
are also used as Special Handling Codes.
Meaning Abbr Code Notes
Context:
Active Temperature Controlled System ACT
Aircraft on Ground AOG
Bulk Unitization Programme, Shipper/Consignee Handled Unit BUP
Cargo Aircraft Only CAO
Cargo Attendant Accompanying Shipment CAT

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Cargo Has Not Been Secured Yet for Passenger or All-Cargo 
Aircraft NSC
Secure for Passenger, All-Cargo and All-Mail Aircraft in Accordance 
with High Risk Requirements SHR
Company Mail COM
Consignment established with a paper air waybill contract being 
printed under an e-AWB agreement ECP
Consignment established with an electronically concluded cargo 
contract with no accompanying paper airwaybill ECC
Control Room Temperature  +15°C to +25°C CRT
Cool Goods COL
Diagnostic Specimens RDS
Diplomatic Mail DIP
e-freight Consignment with Accompanying Paper Documents EAP
e-freight Consignment with No Accompanying Paper Documents EAW
Excepted Quantities of Dangerous Goods REQ
Excepted Quantities of Radioactive Material RRE
Fish/Seafood PES
Flowers PEF
Foodstuffs EAT
Frozen Goods Subject to Veterinary/Phytosanitary Inspections FRI
Frozen Goods FRO
Fruits and Vegetables PEP
Goods Attached to Air Waybill ATT
Hanging Garments GOH
Hatching Eggs HEG
Heavy Cargo/150 kilograms and over per piece HEA
Human Remains in Coffin HUM
Hunting trophies, skin, hide and all articles made from or 
containing parts of species listed in the CITES (Convention on 
International Trade in Endangered Species) appendices
PEA
Cargo Secure forAll-Cargo Aircraft Only SCO
Laboratory Animals SPF
Cargo Secure for Passenger and All-Cargo Aircraft SPX
License Required LIC
Live Animal AVI
Living Human Organs/Blood LHO
Mail MAL
Meat PEM
Munitions of War MUW
Newspapers, Magazines NWP
Obnoxious Cargo OBX
Outsized BIG
Overhang Item OHG
Passenger and Cargo PAC
Perishable Cargo PER
Pharmaceuticals PIL

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Priority Small Package XPS
Quick Ramp Transfer QRT
Reserved Air Cargo RAC
Save Human Life SHL
Shipments of Wet Material not Packed in Watertight Containers WET
Sporting Weapons SWP
Surface Transportation SUR
Undeveloped/Unexposed Film FIL
Valuable Cargo VAL
Very Important Cargo  VIC
Volume VOL
Vulnerable Cargo VUN
1.17 Standard Message Identifiers general 101
Meaning Abbr Code Notes
Context: Airport Handling Manual
ULD Control UCM
ULD Stock Check SCM
ULD/Bulk Load Weight Signal UWS
Context: Cargo-IMP Manual
Adjustment Request FAR
Advice of Discrepancy FAD
Air Waybill Charges Collect FWC
Air Waybill Data FWB
Air Waybill Data Request FWR
Airline Confirmation FAC
Airline Flight Manifest FFM
Allotment Information Request FOR
Allotment Information Answer FOA
AWB Space Allocation Answer FFA
AWB Space Allocation Change FFC
AWB Space Allocation Request FFR
Cancellation FXX
Cancellation of Embargo FMX
CASS Advice of Correction CAC
CASS Debit/Credit Memorandum DCM
CASS Invoice FCI
CASS Remittance FCR
CASS Void/Cancel Air Waybill FCV
CCS Free Text FYT
Change of Embargo FMC
Charges Correction Acknowledgement FCA
Charges Correction Request FCC
Consolidation List FHL
Courier Baggage Voucher FBV
Customs Inventory Report CIR

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Customs Supplementary Information CSI
Customs Status Notification CSN
Declaration for Dangerous Goods Data FDD
Discrepancy Answer FDA
Error FNA
Freight Agent Information FAI
Freight Agent Supplementary Information FAS
Freight Booked List FBL
Freight Booked List Request FBR
Freight CASS Billing FCB
Freight Transaction FFT
General Status Request STR
General Status Answer STA
House Waybill Data FZB
House Waybill Data Request FZA
House Waybill Data Answer FZD
House Waybill Status Request FZC
House Waybill Status Update FZE
Irregularity Report FRP
Mail Advisory MAM
Mail Label Data MLD
Message Acknowledgement FMA
Multiple Status Update List FSL
Notification of Embargo FMB
Piece Manifest FPM
Piece Manifest Request FMR
Piece Status Answer FPA
Piece Status Request FPR
Piece Status Update FPU
Rate Information Answer FTA
Rate Information Request FTR
Schedule and Availability Information Answer FVA
Schedule and Availability Information Request FVR
Shipment Charge Calculation Answer FQA
Shipment Charge Calculation Request FQR
Status Answer FSA
Status Request FSR
Status Update FSU
Substitute Air Waybill Data FSB
Supplementary Rate Information Answer FRA
Supplementary Rate Information Request FRR
Surface Transportation Booking Answer SBA
Surface Transportation Booking Request SBR
Surface Transportation Charges Information SCI

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Surface Transportation Movement STM
Surface Transportation Planning Answer SPA
Surface Transportation Planning Cancellation SPX
Surface Transportation Planning Request SPR
Surface Transportation Status Update SSU
Unit Load Device Manifest FUM
ULD Space Allocation Answer FUA
ULD Space Allocation Request FUR
Context: Systems and Communications Reference Manual
Correction to Previous Message COR
Possible Duplicate Message PDM
Context: ULD Control Manual
Multilateral ULD Control MUC
ULD Exchange Control LUC
ULD Transaction Rejection UTR
1.18 Status Codes general 400
Meaning Abbr Code Notes
Context:
An apparent error has occurred, on this date at this location, with 
the handling of the consignment or its documentation, which is 
further clarified by the accompanying discrepancy code
DIS
The arrival documentation has been physically delivered to the 
consignee or the consignee’s agent on this date at this location AWD
The arrival documentation has been physically received from a 
scheduled flight at this location AWR
The consignee or the consignee’s agent has been notified, on this 
date at this location, of the arrival of the consignment NFD
The consignment has arrived on a scheduled flight at this location ARR
The consignment has been booked for transport between these 
locations on this scheduled date and this flight BKD
The consignment has been cleared by the Customs authorities on 
this date at this location CCD
The consignment has been manifested and/or will be physically 
transferred to this carrier at this location TRM
The consignment has been manifested for this flight on this 
scheduled date for transport between these locations MAN
The consignment has been physically delivered to the consignee or 
the Consignee’s agent on this date at this location DLV
The consignment has been physically delivered to the consignee’s 
door on this date at this location DDL
The consignment has been physically received from a given flight 
or surface transport of the given airline RCF
The consignment has been physically received from the shipper or 
the shipper’s agent and is considered by the carrier as ready for 
carriage on this date at this location
RCS
The consignment has been physically received from this carrier on 
this date at this location RCT
The consignment has been physically transferred to this carrier on 
this date at this location TFD
The consignment has been prepared for loading on this flight for 
transport between these locations on this scheduled date PRE
The consignment has been reported to the Customs authorities on 
this date at this location CRC

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
The consignment has been transferred to Customs/Government 
control TGC
The consignment has physically departed this location on this 
scheduled date and flight for transport to the arrival location DEP
The consignment is on hand on this date at this location pending 
“ready for carriage” determination FOH
Documents Received by Handling Party DOC
1.19 Line Identifiers general 103
Meaning Abbr Code Notes
Context:
          Accounting
          Information ACC
Agent AGT
Agent Reference Data ARD
Air Waybill Piece Information API
Airline Header AIR
Allotment Availability Information ALA
Allotment Information ALI
Allotment Remaining ALR
Allotment Total ALT
Allotment Used Details AUD
Also Notify NFY
Amendment Identification AMD
Arrival Information Details AID
Authorisation ATH
Availability Supplementary Details AVS
AWB Amount Detail Information ABI
AWB Charge Summary ACS
AWB Consignment Details ACD
AWB Content Certification CER
AWB Issue Details ISU
AWB Recapitulation Information ARI
AWB Supplementary Information ABS
AWB Total Amount Information ABT
AWB Total Weight Summary ATW
Baggage Detail Information BGD
Baggage Tag Identification BGT
Booking References REF
Broker BRK
Cargo Control Location CCL
Carrier Reference Data CRD
CASS AWB Information CWI
CASS Billing Details CBD
CASS Billing Information CBI
CASS Billing Period CBP

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
CASS Identification Number CIN
CASS Invoice Header Details CIH
CC Charges in Destination Currency CDC
CCA/Adjustment Information CAI
CCA/Adjustment Supplementary Information CAS
CCA/Adjustment Total Information CTI
CCA/Adjustment Total Weight Summary CTW
Charge Calculation Answer Details RQD
Charge Calculation Answer Totals RQT
Charge Calculation Request Header RQH
Charge Calculation Request — ULD RQU
Charge Calculation Request — Volume RQV
Charge Declarations CDI
Charge Declarations CVD
Collect Charge Summary COL
Commission Information COI
Consignee CNE
Consignee Name and Address CNE
Consignment Control Details CCD
Consignment Onward Movement Information CMI
Correction Identification CID
Courier Baggage Receiver CBR
Courier Baggage Sender CBS
Courier Baggage Voucher Identification CBV
Currency Details CUR
Customer Identification CUS
Customs Action Notification CAN
Customs Notification Details CND
Customs Origin COR
Date/Time of Notification DTN
Declarant DCL
Despatch Information DES
DGD Additional Handling Information DAI
DGD “All Packed in One” Indication DAP
DGD “All Packed in One” Total DAT
DGD Emergency Contact Information DCI
DGD Header Details DHD
DGD Item Authorisation DAU
DGD Item Information DII
DGD Item Number DNR
DGD Item Packing Group and Instructions DPI
DGD Item Quantity and Type of Packing DQP
DGD Item Shipping Name DSN
DGD Item Technical Name DTN

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
DGD Overpack Summary DOS
DGD Radioactive Activity Information DRA
DGD Radioactive Consignment Information DRC
DGD Radioactive Packing Instructions DRP
DGD Signatory Details DSU
Dimensions Information DIM
Documentation Identification DOC
Embargo Carriage Restrictions CRR
Embargoed Commodities COM
Embargo Justification JST
Embargo Routes/Areas RTS
Empty Equipment in Compartment Information EIC
Export EXP
Flight Booking FLT
Flight Information FLT
Free Text Description TXT
Grand AWB Recapitulation Information GRI
          Grand Total
          Information GTI
Handling Details HDL
Harmonised Tariff Schedule Information HTS
House Waybill HWB
House Waybill Piece Information HPI
HWB Agent’s Head Office HAH
HWB Consignment Details HCD
HWB Letter of Credit Details HLC
House Waybill Summary Details HBS
Import IMP
Invoice Total Amount Information ITA
Invoice Total Weight Summary ITW
Location LOC
Mail MAL
Mail Consignment Header MCH
Mail Consignment Total MCT
Mail Handling Unit MHU
Mail Inbound Data MID
Mail Label Identification MLI
Mail Outbound Data MOD
Mail Status Details MSD
Mail ULD Information MUD
Master Waybill Identification MBI
Message Sequence and ULD Origin MSU
Message Advice Type MAT

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Movement Priority Information MPI
Name NAM
Net Billing Information NBI
Net/Net Sales NNS
New Information NEW
Nominated Agent AGT
Nominated Agent Coded AGT
Nominated Agent/Consignee AGT
Nominated Handling Party NOM
Notify Name and Address NFY
Original Information OLD
Other Charges OTH
Other Customs, Security and Regulatory Control Information OCI
Other Participant Information OPI
Other Service Information OSI
Passenger Information PAS
Prepaid Charge Summary PPD
Planning Request Details PRD
Product Information PID
Rate Description RTD
Rate Information Answer Details RID
Rate Information Answer Header RIH
Rate Information Request Details RIR
Reason for Acknowledgement ACK
Recapitulation Amount Information RCI
Recapitulation Total Information RTI
Receptacle Information REC
Request Reference REF
Routing RTG
Sales Incentive Information SII
Schedule and Availability Information Request Details SAR
Schedule and Availability Information Answer Details SAA
Schedule Information Answer Header SKH
Sender Reference REF
Shipment Reference Information SRI
Shipper SHP
Shipper Name and Address SHP
Special Customs Information SCI
Special Handling Details SPH
Special Service Request SSR
Status Details STS
Status List Criteria SLC
Storage Information STI
Street Address ADR

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Supplementary Rate Information Answer Details SRA
Supplementary Rate Information Request Details SRR
Supplementary Status Information SSI
Surface Charge Summary SCS
Surface Delivery Information SDI
Surface Pickup Information SPI
Surface Vehicle Arrival Information SVA
Surface Vehicle Delay Information SVL
Surface Vehicle Departure Information SVD
Surface Vehicle Next Information SVN
Tax Summary TXS
Terminal Identification TID
The Regulated Agent Accepting   the Security Status for a 
Consignment Issued by Another Regulated Agent OSS
The Regulated Agent Issuing the Security Status for a 
Consignment ISS
Total Amount TOT
Total AWB Recapitulation Information TAR
Total Collect Charges TCC
Transfer/Transit Information TRN
Transit TRA
ULD Connection Information UCI
ULD Description ULD
ULD Destination Information UDI
ULD Inclusion Information UII
ULD Movement Information UMI
Unique Piece Information UPI
Vehicle Operator Details VOD
Void/Cancel Details VCD
Waybill Details WBD
Waybill Details WBL
Waybill Header Details WBH
Waybill Identification WBI
Waybill Information WBI
1.20 ULD Volume Available Codes general 803
Meaning Abbr Code Notes
Context:
          No Volume
          Available 0
More Than One Quarter Volume Available 1
More Than One Half Volume Available 2
More Than Three Quarters Volume Available 3
1.21 ULD Condition Codes general 806
Meaning Abbr Code Notes
Context:

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Damaged But Still Serviceable DAM
Serviceable SER
1.22 Volume Codes general 604
Meaning Abbr Code Notes
Context:
Cubic Centimetres CC
Cubic Feet CF
Cubic Inches CI
Cubic Metres MC
1.23 Density Group Indicator general 603
Meaning Abbr Code Notes
Context:
Density Group DG
1.24 Weight Codes general 601
Meaning Abbr Code Notes
Context:
Kilos K
Pounds L
1.26 ULD Loading Codes general
Meaning Abbr Code Notes
Context:
Nose Cargo Door — ULD NCD
Pallet with Extensions (Wings) PWG
Side Cargo Door — ULD SCD
ULD Loaded on the main deck which will also fit into a lower deck 
position PLD
ULD Loaded on the main deck which will not fit into a lower deck 
position PMD
1.27 Quantity Identifiers general 712
Meaning Abbr Code Notes
Context:
Boarded Quantity B
Received Quantity R
1.28 Goods Data Identifiers general 710
Meaning Abbr Code Notes
Context:
Consolidation C
Country of Origin of Goods O
Dimensions D
Goods Description G
Harmonised Commodity Code H
Shipper’s Load and Count S
ULD Number U
Volume V
1.29 Handling Detail Identifiers general 413
Meaning Abbr Code Notes
Context:
Also Notify Instructions NFY

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Special Handling Details SPH
Special Service Request SSR
1.30 Accounting Information Identifiers general 411
Meaning Abbr Code Notes
Context:
Credit Card Number (see GEN6)
CRN
As per "Payment Card Industry Data Security Standards(PCI DSS)", 
masking shall be applicable to the credit card number display, a 
maximum of the first six and last four digits (1234 56XX XXXX 7890) 
can be displayed.
Credit Card Expiry Date CRD
Credit Card Issuance Name (Name Shown on the Credit Card) CRI
General Information GEN
Government Bill of Lading GBL
Miscellaneous Charge Order MCO
Mode of Settlement STL
Return to Origin RET
Shipper’s Reference Number SRN
1.31 No Value Codes general
Meaning Abbr Code Notes
Context: Carriage
No Value Declared NVD
Context: Customs
No Customs Value NCV
Context: Insurance
No Value XXX
1.32 AWB Column Identifiers general 105
Meaning Abbr Code Notes
Context:
Charge/Rate Details R
Chargeable Weight Details W
Item (Line) Charge Total Details T
Nature of Goods Details N
Number of Pieces/RCP Details P
Rate Class Details C
Secondary Rate Info (Commodity) Details S
Weight Details K or L
1.33 Charge Identifiers general 502
Meaning Abbr Code Notes
Context:
CASS Invoice Amount NI
CASS Net Amount CN
Charge Summary Total CT
Commission CO
Insurance IN
Sales Incentive SI
Taxes TX
Total Other Charges Due Agent OA
Total Other Charges Due Carrier OC

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Total Weight Charge WT
Valuation Charge VC
1.34 Office Function Designators general 107
Other Office Function Designators besides these 
listed may be included in Cargo-IMP messages.
Meaning Abbr Code Notes
Context:
Freight/Cargo Handling — General Function FF
Freight/Cargo Reservations — General Function FR
Freight/Cargo Systems Address FM
1.35 Master AWB Indicator general 120
Meaning Abbr Code Notes
Context:
Master AWB Indicator M
1.36 Participant Identifiers general 319
Meaning Abbr Code Notes
Context:
Airline AIR
Airport Authority APT
Agent AGT
Broker BRK
Commissionable Agent CAG
Consignee CNE
Customs CTM
Declarant DCL
Deconsolidator DEC
Freight Forwarder FFW
Ground Handling Agent GHA
Post Office PTT
Shipper SHP
Trucker TRK
1.37 Domestic/International Indicators general 416
Meaning Abbr Code Notes
Context:
Domestic Indicator D
International Indicator I
1.38 Service Codes general 505
Service codes besides these listed may be used 
on a proprietary basis within Cargo-IMP 
messages.
Meaning Abbr Code Notes
Context:
Airport-to-Airport A
Airport-to-Door E
Charter T
Company Mail H
Company Material C
Diplomatic Mail I
Door-to-Airport G
Door-to-Door Service D

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Express Shipments X
Flight Specific F
Priority Service J
Service Shipment B
Small Package Service P
Substitute Truck S
1.39 Contact Identifiers general 122
Meaning Abbr Code Notes
Context:
Telefax FX
Telephone TE
Telex TL
1.40 Days of the Week general 204
Meaning Abbr Code Notes
Context:
Monday 1
Tuesday 2
Wednesday 3
Thursday 4
Friday 5
Saturday 6
Sunday 7
1.41 Day Change Indicators general 205
Meaning Abbr Code Notes
Context:
Day -1 (Previous) P
Day +1 (Next) N
Day +2 (Second) S
Day +3 (Third) T
Day +4 A
Day +5 B
Day +6 C
Day +7 D
Day +8 E
Day +9 F
Day +10 G
Day +11 H
Day +12 I
Day +13 J
Day +14 K
Day +15 L
1.42 Connection Restriction Indicators general 419
Meaning Abbr Code Notes
Context:
Excluding such Connection E
Limited to such Connection L

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
No Connection N
1.43 Rate Type Codes general 515
Meaning Abbr Code Notes
Context:
All Rates ALL
General Commodity Rate GCR
Specific Commodity Rate SCR
ULD Rate ULD
1.44 ULD Charge Codes general 516
Meaning Abbr Code Notes
Context:
First Minimum Charge — minimum weight B
First over pivot rate per kilogram C
Flat Charge — maximum weight I
Flat Charge — (without weight or with minimum weight) H
Pivot Rate per kilogram A
Second Minimum Charge — minimum weight D
Second over pivot rate per kilogram E
Third Minimum Charge — minimum weight F
          Third over pivot rate
          per kilogram G
1.45 Rate Information Types general 518
Meaning Abbr Code Notes
Context:
Commodity Item Number C
Rate Note N
ULD Charge Code U
1.46 Aircraft Possibility Codes general 809
Meaning Abbr Code Notes
Context:
Mixed configuration (Combi) aircraft carrying Loose Load Cargo on 
the passenger deck BBQ
Mixed configuration (Combi) aircraft carrying Containerized Cargo 
(ULDs) on the passenger deck LLQ
Mixed configuration (Combi) aircraft carrying Containerized 
(ULDs)/Palletized Cargo on the passenger deck LPQ
Mixed configuration aircraft carrying Palletized Cargo on the 
passenger deck PPQ
Passenger flight operated by wide-bodied aircraft carrying 
Palletized Cargo PPJ
Passenger flight operated by wide-bodied aircraft carrying 
Containerized (ULDs) LLJ
Passenger flight operated by wide-bodied aircraft carrying 
Containerized (ULDs)/ Palletized Cargo LPJ
Pure freighter flight carrying Containerized Cargo (ULDs) LLF
Pure freighter flight carrying Containerized (ULDs)/Palletized Cargo
LPF
Pure freighter flight carrying Loose Load Cargo BBF
Pure freighter flight carrying Palletized Cargo PPF

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Truck carrying Containerized Cargo (ULDs) LLV
Truck carrying Containerized (ULDs)/Palletized Cargo LPV
Truck carrying Loose Load Cargo BBV
Truck carrying Palletized Cargo PPV
1.47 ULD Loading Indicators general 811
Meaning Abbr Code Notes
Context:
Main Deck Loading only M
Nose Door Loading only N
ULD Height below 160 centimetres L
ULD Height between 160 centimetres and 244 centimetres U
ULD Height above 244 centimetres R
1.48 Measurement Unit Code general 611
Other than NDA, these codes are extracted or 
derived from those listed in UN/ECE 
Recommendation 20.
Meaning Abbr Code Notes
Context:
Becquerel BQL
Centigram CGM
Centilitre CLT
Centimetre CMT
Curie CUR
Decilitre DLT
Decimetre DMT
Fluid Ounce (28.413 CM3) OZI
Fluid Ounce (29.5795 CM3) OZA
Foot FOT
Gallon (4.546092 DM3) GLI
Gigabecquerel GBQ Gill (0.142065 DM3) GII
Gill (11.8294 CM3) GIA
Gram GRM
Inch INH
Kilobecquerel KBQ
Kilogram KGM
Liquid Gallon (3.78541 DM3) GLL
Liquid Pint (0.473176 DM3) PTL
Liquid Quart (0.946353 DM3) QTL
Litre (1 DM3) LTR
Megabecquerel MBQ
Metre MTR
Milligram MGM Millilitre MLT
Millimetre MMT
No Dimensions Available NDA
Ounce UK, US (28.949523 GRM) ONZ
Pint (0.568262 DM3) PTI
Pound UK, US (0.45359237 KGM) LBR

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Quart (1.136523 DM3) QTI
Terabecquerel TBQ
Yard (0.9144 MTR) YRD
1.49 Customs Origin Codes general 906
Meaning Abbr Code Notes
Context:
List to be provided by local customs authorities
1.50 Miscellaneous Codes (Coding) general
Meaning Abbr Code Notes
Context:
Acknowledge ACK
Action Identifier used in lieu of airline code YY or YYY
Add (ed) (ing) AD
Advise (ed) (ing) ADV
Advise Acceptance ADAC
Advise Air Waybill Number ADAW
Advise if Not Correct ADNO
Air Mail MAIL
Air Parcel Post APPO
Air Waybill AWB
Air Waybill Later AWBL
Arrival Not Known ARNK
Arrive(s) (ed) (ing) ARR
Authority (isation) (ised) AUTH
Ballast BAL
Believe BLV
Cancel (lation) QTA
Cargo CGO
Cargo Charges Correction Advice CCA
Change Weight CHWT
Charter CHTR
Clarify — Your Message Not Understood CFY
Commercial Invoice COMI
Confirm (ed) (ation) CFM
Connection CONX
Consignee CNEE
Consignee Notified CNAD
Consignment/Shipment SHPT
Contact (ed) (ing) CTC
Delay Account of DDUE
Dimensions DIMS
Disposition DISP
Do All Possible DAPO
Document (s) (ation) DOCS
Estimated Time of Arrival ETA

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Estimated Time of Departure ETD
Express Waybill EWB
First Available FRAV
Flight FLT
Forward (ed) (ing) FWD
Government Bill of Lading GBL
House Waybill HWB
Identification ID
If Unable To IFUN
Import License IMLI
Insurance IN
Invalid INVLD
Irregularity Report/Notice of Non-Delivery IRP
Master Air Waybill MWB
Miscellaneous Charges Order MCO
Missed Connection MSCONX
My Letter (Memorandum etc.) ML
My Telegram (Cable, Message, Telex, Wire) MT
Neutral Air Waybill NWB
No Connection NOCONX
No Operation NOOP
No Recognition/Record NOREC
Notice of Non-Delivery/Irregularity Report IRP
Not Yet Delivered ND
Piece(s) PC
Rate Combination Point RCP
Repeat (ed) (ing) RPT
Request (ed) (ing) REQ
Request for date and flight of arrival or, if available, date of 
delivery or transfer, or advice that shipment is undelivered TRAD
Sequence SEQ
Shipment/Consignment SHPT
Shipper SHPR
Shipper’s Declaration for Dangerous Goods DGD
Shipper’s Letter of Instruction SLI
Shipper Load and Count SLAC
Soon as Possible SASPO
Standard Message Identifier SMI
Substitute Air Waybill SWB
Surface Transportation SUR
Total TTL
Unaccompanied Baggage UBAG
Unit Load Device ULD
Weight WT

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Your Letter (Memorandum etc.) YL
Your Telegram (Cable, Message, Telex, Wire) YT
1.51 Type of Time Indicators general 206
Meaning Abbr Code Notes
Context:
Actual Time A
Estimated Time E
Scheduled Time S
1.60 CCS System Identifiers general 911
Meaning Abbr Code Notes
Context:
Aviation Exchange AVX
Brucargo Community System BCS
Cargo Community Systems Australasia Pty. Ltd. CCS
Cargo Community System Austria CAT
Cargo Community System Carat U.S.A. CUS
Cargo Community System Israel CIL
Cargo Community System Italy CIT
Cargo Community System Singapore CSG
Cargo Community System Switzerland CCH
Cargonaut B.V. The Netherlands CGN
Community System United Kingdom CUK
Equation CGU
Global Logistic System America RUS
Global Logistic System Asia RAS
Global Logistic System Europe REU
Global Logistic System Hong Kong RHK
Global Logistic System Worldwide GLS
INTIS — Port of Rotterdam, The Netherlands INT
Irish Community Air Cargo Realtime Users Systems ICU
Trade-Van Taiwan TVN
Tradevision Scandinavia TDV
U.S.A Cargo Community System USC
ZA Cargo Community System South Africa ZAC
1.61 CCS Code Types general 912
Meaning Abbr Code Notes
Context:
Agent Name or Code 03
Company Designator 09
General Electric (GEIS) 06
IATA Cargo Agent Numeric Code 02
IATA Cargo Agent Numeric Code and IATA Cargo Agent CASS 
Address 10
IATA Teletype Address 01
IBM IN 07
ICAO Carrier Code 08

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
International X25 NUA 04
X400 Address 05
1.62 CCS ID Code Qualifiers general 914
Meaning Abbr Code Notes
Context:
IATA Cargo Z1
1.63 CCS Group Codes general 909
          Participant Identifiers described in 1.36 
are also used as CCS Group Codes.
Meaning Abbr Code Notes
Context:
CCS Central Facility SYS
Unknown CCS Group Code XXX
1.70 Mail Category Codes general 922
Meaning Abbr Code Notes
Context:
Air Mail/Priority Mail A
SAL Mail/non-Priority Mail B
Surface Mail/non-Priority Mail C
1.71 Mail Class Codes general 923
Meaning Abbr Code Notes
Context:
EMS E
Empty Bags T
Letters (LC and AO) U
Parcels (CP) C
1.72 Receptacle Type Codes general 928
Meaning Abbr Code Notes
Context:
Bag BG
Container CN
Parcel out of Bag PC
Tray PU
1.73 Mail Dangerous Goods Indicator general 930
Meaning Abbr Code Notes
Context:
Mail Consignment Comprising Dangerous Goods Y
1.74 Mail Handling Class Codes general 931
Meaning Abbr Code Notes
Context:
Insured V
Normal N
Registered R
1.75 Mail ULD Type Codes general 924
Meaning Abbr Code Notes
Context:
List to be provided by UPU
1.76 Mail Sub-Class Codes general 927
Meaning Abbr Code Notes

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Context:
List to be provided by UPU
1.77 Text Subject Qualifiers general 125
Meaning Abbr Code Notes
Context:
General Information ING
Mail MAL
Specific Information INS
Trucker Manifest TKM
1.78 Credit Amount Indicators general 519
Meaning Abbr Code Notes
Context:
Credit Amount CR
1.79 Tax Identification Codes general 520
Meaning Abbr Code Notes
Context:
Goods and Service Tax (GST) GS
Quebec Sales Tax (QST) QS
Tax on Commission TC
Value Added Tax VA
1.80 CASS Indicators general 614
Meaning Abbr Code Notes
Context:
AWB as Invoice I
Cancel AWB C
Charges Correction Advice CC
Debit or Credit Memorandum DC
Identification ID
Late Reporting Waybills L
No Commission or Negative Sales Incentive N
Original Data DL
Revised (adjusted) Data AD
Service AWB S
Tax Calculation Required T
Void AWB V
1.81 HWB As Agreed general 128
Meaning Abbr Code Notes
Context:
HWB As Agreed A
1.82 DG UN or ID Prefix general 716
Meaning Abbr Code Notes
Context:
Identification ID
United Nations UN
1.83 Overpack Indicator general 719
Meaning Abbr Code Notes
Context:
Overpack Indicator O

Rev Image Ref No Abbr Name Type Data Element Notes
1.84 Category Colour general 728
Meaning Abbr Code Notes
Context:
White W
Yellow Y
1.85 Fissile Excepted Indicator general 730
Meaning Abbr Code Notes
Context:
Fissile Excepted Y
1.86 LSA/SCO Indication general 731
Meaning Abbr Code Notes
Context:
Low Specific Activity LSA
Surface Contaminated Object SCO
1.87 Allotment Status Code general 421
Meaning Abbr Code Notes
Context:
Closed C
Deleted D
Full F
Open O
Pending P
1.88 Type of Information Indicator general 207
Meaning Abbr Code Notes
Context:
History of Statuses H
List of Allotments L
Status of Allotment(s) S
1.89 Surface Charge Identifiers general 521
Meaning Abbr Code Notes
Context:
Convention Material CM
Collect Charges Fee FC
Inside Pickup/Delivery IS
Location Charge LC
Lift Gate Charge LG
Outbound Document Fee OB
Personal Effects PE
Special Surcharge SL
Waiting Time WT
1.90 Delivery/Pickup Indicators general 422
Meaning Abbr Code Notes
Context:
Delivery D
Pickup P
1.91 Loading Order Indicators general 423
Meaning Abbr Code Notes
Context:
Loading Order Indicators Y

Rev Image Ref No Abbr Name Type Data Element Notes
1.92 Movement Indicators general 815
Meaning Abbr Code Notes
Context:
Actual Arrival AA
Actual Departure AD
Estimated Arrival EA
Estimated Departure ED
Delayed DL
Next Information NI
Scheduled Arrival SA
Scheduled Departure SD
1.93 Bar Code Types general 934
Meaning Abbr Code Notes
Context:
Journey Identification J
Receptacle R
Unit Load Device U
Belly Cart (not air worthy) B
General Container G
1.94 Expected Indicators general 935
Meaning Abbr Code Notes
Context:
Expected Y
Not Expected N
1.95 Mail Status Event Codes general 936
Meaning Abbr Code Notes
Context:
Attempted Delivery to Designated Postal Operator ATT
Delivered to Designated Postal Operator DLV
Mail Recevied from flight at Warehouse RCF
Received from another airline RCT
Received from Designated Postal Operator REC
Receptacal nested into a ULD NST
Returned to Designated Postal Operator RET
Staged/Planned for a flight STG
Transferred to another airline TFD
1.96 Mail Mode general 938
Meaning Abbr Code Notes
Context:
Handler/Carrier H
Designated Postal Operator G
Flight F
1.97 Piece Identification Indicators general 138
Meaning Abbr Code Notes
Context:
Assigned and included I
Assigned and available but not included A
Not assigned or available N

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Required R
1.98 Customs Duty Indicators general 424
Meaning Abbr Code Notes
Context:
Dutiable Y
Non-Dutiable N
1.99 ULD Contour Codes general 817
Meaning Abbr Code Notes
Context:
10FT, Height < 160CM and no wing PLD
10FT, Height < 160CM and winged PWG
10FT, Height < 160CM, half width and winged on one side only 
(Half PWG) PHW
10FT, Height > 160CM but < 240CM Q6
          10FT, Height > 160CM
          but < 240CM and contoured for A1 (F) position A1
10FT, Height > 160CM but < 240CM and contoured for A2 (A) 
position A2
10FT, Height > 240CM but < 300CM Q7
16 or 20FT, Height > 160CM but < 240CM S6
16 or 20FT, Height > 240CM but < 300CM S7
1.100 Customs, Security and Regulatory Contr general 941
Full detailed descriptions for RA, KC & AC are 
contained in Cargo Services Conference 
Recommended Practice 1630 CARGO SECURITY
 T (Trader Identification Number) can also be 
used to identify Economic Operator Registration 
Identification (EORI) number
 M (Movement Reference Number) can also be 
used to identify similar numbers in other 
countries, e.g. an Internal Transaction Number 
for the US or an Export Authorization Number in 
Canada
Meaning Abbr Code Notes
Context:
Account Consignor  (consignor for all cargo aircraft only) AC
Authorised Economic Operator E
Automated Broker Interface (ABI) Filer Code A
Certificate Number C
Dangerous Goods D
Exemption Legend L
Invoice Number V
Item Number I
Facilities Information and Resource Management Systems (FIRMS) 
Code F
Known Consignor  (consignor for both passenger and all cargo 
aircraft only) KC
Movement Reference Number M
Packing List Number P
Regulated Agent RA
Regulated Carrier RC
License Identification (e.g. export licenses,Kimberly licenses) LI

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Declaration Identification (e.g. letter for lithium batteries) DI
Screening Method SM
Security Status Date and Time SD
Security Status Name of Issuer SN
Security Status SS
Security Textual Statement ST
Expiry Date ED
Seal Number N
System Downtime Reference S
Trader Identification Number T
Unique Consignment Reference Number U
1.101 Quantity Indicator general 733
Meaning Abbr Code Notes
Context:
Gross G
Net N
1.102 Screening Methods general 942
Meaning Abbr Code Notes
Context:
Physical Inspection and/or Hand Search PHS
Visualcheck VCK
X-ray Equipment XRY
Explosive Detection System EDS
Remote Explosive Scent Tracing Explosive Detection Dogs RES
Free Running Explosive Detection Dogs FRD
Vapor Trace VPT
Particle Trace PRT
Metal Detection Equipment MDE
Subjected to Flight Simulation SIM
Subjected to Any Other Means AOM
1.103 Security Statuses general 943
Meaning Abbr Code Notes
Context:
Cargo Has Not Been Secured Yet for Passenger or All-Cargo 
Aircraft NSC
Cargo Secure for Passenger and All-Cargo Aircraft SPX
Cargo Secure for All-Cargo Aircraft Only SCO
Secure for Passenger, All-Cargo and All-Mail Aircraft in Accordance 
with High Risk Requirements SHR
1.104 Screening Exemptions general 944
Meaning Abbr Code Notes
Context:
Small Undersized Shipments SMUS
Mail MAIL
Bio-Medical Samples BIOM
Diplomatic Bags or Diplomatic Mail DIPL
Life-Saving Materials (Save Human Life) LFSM

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Abbr Code Notes
Nuclear Material NUCL
Transfer or Transshipment TRNS
1.105 Mail Handling Unit Types general 945
Meaning Abbr Code Notes
Context:
Belly Cart (not air worthy) B
General Container (air worthy) G
2. Density Group Codes density
It should be noted that this information should 
serve only as a guideline and the density of 
certain commodities may be different and related 
to the country of origin of the goods.
In cases where commodity is not adequately 
defined, density group 6 must be used.
Meaning Category
Context: (0) 160kg per mc or 10 lbs per cf 
Fruit (0)
Household Appliances (0)
Laboratory Equipment (0)
Leather Gloves (0)
Optical Material (0)
Tires — Rubber (0)
Vegetables (0)
Wigs (0)
Context: (1) 300 kg per mc or 18.6 lbs per cf 
Calculators (1)
Cash Registers (1)
Drugs (1)
Films (1)
Hand Tools (1)
Magnetic Tapes (1)
Pharmaceutical Products (1)
Radio Transmitting — TV Equip (1)
Telephone/Telegraph Equipment (1)
Tractor Parts (1)
Typewriters (1)
Context: (10) 950 kg per mc or 59.3 lbs per cf 
Liquids (0)
Context: (2) 90 kg per mc or 5.6 lbs per cf 
Athletic/Sporting Goods (2)
Consolidations (2)
Flowers (2)
Footwear (2)
Glassware (2)
Leather Bags (2)
Plastic Products (2)
Radio Transmitting — TV Equip (2)
Telephone/Telegraph Equipment (2)
Tractor Parts (2)

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Category
Toys (2)
Context: (3) 120 kg per mc or 7.5 lbs per cf 
Clothing/Apparel (3)
Knitted Goods (3)
Live Animals (3)
Military Pribag (3)
Musical Instruments (3)
Personal Effects (3)
Radioactive Material (3)
Rubber Products (3)
Wooden Articles (3)
Context: (4) 220 kg per mc or 13.8 lbs per cf 
Advertising Signs/Displays (4)
Carpets (4)
Diplomatic Mail (4)
Documents (4)
Electrical Material/Apparatus (4)
Electronic Equipment/Parts (4)
Furs/Furskins (4)
Live Plants (4)
Office Machines (4)
Recording Machines (4)
Tape Recorders (4)
Textiles (4)
Context: (5) 60 kg per mc or 3.8 lbs per cf 
Automobiles (5)
Live Birds (5)
Luggage — Empty (5)
Speakers (5)
Context: (6) 250 kg per mc or 15.6 lbs per cf 
Aircraft Parts (7)
Auto Parts (7)
Cameras/Camera Equipment (7)
Cosmetics (7)
Food Preparations (7)
Human Remains — Not Cremated (7)
Medical Instruments (7)
Military Stores/Impediments (7)
Office Supplies (7)
Paper Products (7)
Toiletries (7)
Context: (8) 400 kg per mc or 25 lbs per cf 
Adhesives (8)
Chinaware (8)
Compressors (8)

Rev Image Ref No Abbr Name Type Data Element Notes
Meaning Category
Engines, Diesel/Combustion (8)
Frozen Meat (8)
Generators (8)
Machine Parts (8)
Magazines/Periodicals (8)
Newspapers (8)
Pipe Fittings (8)
Printed Matter (8)
Wire Products (8)
Context: (9) 600 kg per mc or 37.5 lbs per cf 
Bearings (9)
Bolts/Nuts/Screws (9)
Building Material (9)
Chemical Products (9)
Electrical Motors (9)
Leather (9)
Machines Industrial (9)
Paint (9)
Pumping Equipment (9)
Records (9)
Valuables (Gold-Jewels-Coin) (9)
Watches (9)

User Capability grid