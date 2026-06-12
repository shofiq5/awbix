import frappe
from frappe.model.document import Document


class Shipment(Document):
	def validate(self):
		self.validate_awb_serial_number()
		self.set_awb_number()
		if self.origin and self.destination and self.origin == self.destination:
			frappe.throw("Origin and Destination cannot be the same airport.")

	def set_awb_number(self):
		if self.airline_prefix and self.awb_serial_number:
			self.awb_number = f"{self.airline_prefix}-{self.awb_serial_number}"

	def validate_awb_serial_number(self):
		serial = (self.awb_serial_number or "").strip()
		if not serial:
			return
		if not serial.isdigit() or len(serial) != 8:
			frappe.throw("AWB Serial Number (DE113) must be exactly 8 digits.")
		# DE113: the last digit is the unweighted modulus-7 check digit of the
		# first seven digits (IATA CSC Resolution 600a).
		expected = int(serial[:7]) % 7
		if expected != int(serial[7]):
			frappe.throw(
				f"Invalid AWB check digit: serial ends in {serial[7]} but the "
				f"modulus-7 check digit of {serial[:7]} is {expected}."
			)
