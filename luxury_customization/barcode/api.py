"""Barcode scan API that returns every item when one barcode is shared by several items."""

import json

import frappe
from frappe import _

from erpnext.stock.utils import _update_item_info
from erpnext.stock.utils import scan_barcode as erpnext_scan_barcode


@frappe.whitelist()
def scan_barcode(search_value: str, ctx: dict | str | None = None):
	matches = get_barcode_items(search_value)
	if len(matches) < 2:
		return erpnext_scan_barcode(search_value, ctx)

	return {"multiple_items": matches}


@frappe.whitelist()
def resolve_barcode_item(barcode: str, item_code: str, ctx: dict | str | None = None):
	"""Return the normal scan result for the item the user picked."""
	match = next((row for row in get_barcode_items(barcode) if row.item_code == item_code), None)
	if not match:
		frappe.throw(_("Barcode {0} does not belong to Item {1}").format(barcode, item_code))

	data = frappe._dict(barcode=match.barcode, item_code=match.item_code, uom=match.uom)
	return _update_item_info(data, parse_ctx(ctx))


def get_barcode_items(barcode: str) -> list[frappe._dict]:
	frappe.has_permission("Item", ptype="select", throw=True)

	item_barcode = frappe.qb.DocType("Item Barcode")
	item = frappe.qb.DocType("Item")
	rows = (
		frappe.qb.from_(item_barcode)
		.join(item)
		.on(item.name == item_barcode.parent)
		.select(
			item_barcode.barcode,
			item_barcode.uom,
			item.name.as_("item_code"),
			item.item_name,
		)
		.where(
			(item_barcode.barcode == barcode)
			& (item_barcode.parenttype == "Item")
			& (item.disabled == 0)
			& (item.has_variants == 0)
		)
		.orderby(item.name)
		.run(as_dict=True)
	)

	return [row for row in rows if frappe.has_permission("Item", ptype="select", doc=row.item_code)]


def parse_ctx(ctx):
	if isinstance(ctx, str):
		ctx = json.loads(ctx)
	return frappe._dict(ctx or {})
