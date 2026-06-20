"""FSA/14 (Freight Status Advice, Cargo-IMP) inbound parser.

Structurally identical to FSU/14 — same consignment-detail line, same repeating status
sections, same SHP FSU target. Only the SMI line differs (FSA/14 vs FSU/14).
"""

from awbix.edx.handlers.fsu.fsu_parser import FSUParser


class FSAParser(FSUParser):
	message_type = "FSA"
	version = "14"
	# parse / business_key / validate / process all inherited from FSUParser unchanged.
	# _strip_preamble already accepts both FSU and FSA via ^(?:FSU|FSA)/\d.
	# parse() reads self.message_type / self.version so the dict reports FSA/14 correctly.
