"""Item override that allows the same barcode on several items."""

import barcodenumber
import frappe
from frappe import _

from erpnext.stock.doctype.item.item import InvalidBarcode, Item, convert_erpnext_to_barcodenumber


class CustomItem(Item):
	def validate_barcode(self):
		"""Same as ERPNext, without the check against other items' barcodes."""
		options = frappe.get_meta("Item Barcode").get_options("barcode_type").split("\n")
		seen = set()

		for row in self.barcodes:
			if not row.barcode:
				continue

			if row.barcode in seen:
				frappe.throw(_("Row #{0}: Barcode {1} is repeated in this item").format(row.idx, row.barcode))
			seen.add(row.barcode)

			row.barcode_type = row.barcode_type if row.barcode_type in options else ""
			if row.barcode_type:
				validate_barcode_type(row)


def validate_barcode_type(row):
	barcode_type = convert_erpnext_to_barcodenumber(row.barcode_type.replace("-", "").upper(), row.barcode)
	if barcode_type in barcodenumber.barcodes() and not barcodenumber.check_code(barcode_type, row.barcode):
		frappe.throw(
			_("Barcode {0} is not a valid {1} code").format(row.barcode, row.barcode_type),
			InvalidBarcode,
		)
