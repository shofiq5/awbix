Doctype: Shipment and Child Doctype: Shipment Rate Line
On Click on shipment.aut_rate_line button.
Please reset Shipment Rate Line and add aline
line=1
piece=shipment.number_of_pieces
wt_code=shipment.weight_code
gorss_weight=shipment.weight
rate_class_code=Q
chargeable_weight=shipment.chargeable_weight
description=shipment.nature_of_goods
if shipment.console=1 then gds_id=C
if shipment.console=1 then gds_id=G 