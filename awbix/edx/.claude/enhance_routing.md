
Enahnce message routing fatching as below
Scop Shipemtn EDX Message Routing
Fatching logic:

Shipemnt.by_carrier1 = edx_message_routing.carrier_code if dx_message_routing.carrier_code  is blank then ignore condition

Shipemnt.airline_Prefix = dx_message_routing.airline_prefix 
if dx_message_routing.airline_prefix is blank then ignore condition

Shipemnt.origin = dx_message_routing.origin
if dx_message_routing.orign is blank then ignore condition

Shipemnt.destination = dx_message_routing.destination
if dx_message_routing.destination is blank then ignore condition