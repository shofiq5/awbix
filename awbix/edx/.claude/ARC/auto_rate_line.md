On Click parent.auto_rateline button
Please insert RTD/rate line automatically as below
Doctype: Shipment and Child Doctype: shipment Rate Line
On Click on parent.auto_rate_line button.
Please reset parent Rate Line and add aline
line=1
piece=parent.number_of_pieces
wt_code=parent.weight_code
gorss_weight=parent.weight
rate_class_code=Q
chargeable_weight=parent.chargeable_weight
description=parent.nature_of_goods
if parent.console=1 then gds_id=C
if parent.console=0 then gds_id=G 
Commodity_item_no=parent.Commodity_item_no