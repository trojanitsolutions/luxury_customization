"""Remove the unique constraint on Item Barcode.barcode so several items can share one barcode."""

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

DOCTYPE = "Item Barcode"
FIELDNAME = "barcode"


def create_custom_fields():
	make_property_setter(DOCTYPE, FIELDNAME, "unique", 0, "Check", validate_fields_for_doctype=False)
	# keep scans fast once the unique index is gone
	make_property_setter(DOCTYPE, FIELDNAME, "search_index", 1, "Check", validate_fields_for_doctype=False)
	frappe.clear_cache(doctype=DOCTYPE)
	frappe.db.updatedb(DOCTYPE)


def delete_custom_fields():
	frappe.db.delete(
		"Property Setter",
		{"doc_type": DOCTYPE, "field_name": FIELDNAME, "property": ("in", ["unique", "search_index"])},
	)
	frappe.clear_cache(doctype=DOCTYPE)
