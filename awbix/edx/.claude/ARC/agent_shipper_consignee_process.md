
relevant file : fwb16_parser.py, shipment.json
One FWB message process.
Please enhance to implement below behaviour.

if Agent:
System shall check if the agent already exists
by Account or IATA Code or IATA Code+CASS Code
IF exists then use existing agent 
If not exists then create new agent.

If Shipper/Consignee/Notify Party.
Than statically update shipper/consignee/Notify Party directly in Shipment table field. no need to check Pary master table.

Implement above best conventional way