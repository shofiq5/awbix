
 Backend FRAPPE 15 Implementation no frontend implementation for now

EDX (Electronic Data Exchange) Module.
EDX Framework Development
International Enterpise EDI Messaging Engine Standard, Functionality, Heavey message handling capability

Connectivity engigne:
	Message Ingest:
			Connectivity Option : email, SFTP, MQ
			System shall have option to configure email (configurtion option, POP, IMAP, SFTP and should be a option to test incoming and outgoung successfull or failed),  sftp, MQ, Manual
			
 
	-Composer Engine (Message Out)
		-Compose message
		-Verify Message
		-Message out a copy of message would be store here with deliver status
		
	-Parser Engine (Message In)
		-Stage Message Without any Filter all message woudld be satge here
		-Message In . processable message would be moved from stage to message in , Message in Must have a verify option to check the message what values are generation by parser it can be human readable json or table 
		-Parse message (Persare should be independent by message Type and Message Version, I should able to add and activete parser like FWB-16, FHL-5 etc)
		-Process Message- Data Feed into tables. Successfully processed message should insert to message out table with status Delivered to moduel like Shipment
		-Message log

Composer and parser would be by message type and version. Initially We will do only for FWB/16
I will provide complete rule and message manuel.
Implementation should be such way  that i should be able to develop  and add different type message and version in same framework

Phase 2		
EDX Dashboard
A robust message deashboard which allow to filter message and see message in our out screen,  		
		