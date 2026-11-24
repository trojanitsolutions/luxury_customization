import frappe
from frappe.tests import IntegrationTestCase

from luxury_customization.barcode.api import resolve_barcode_item, scan_barcode

SHARED_BARCODE = "LUXSHARED0001"
SINGLE_BARCODE = "LUXSINGLE0001"
ITEMS = ("_Test Lux Barcode Red", "_Test Lux Barcode Blue")


def make_item(item_code, barcodes):
	if frappe.db.exists("Item", item_code):
		frappe.delete_doc("Item", item_code, force=True)

	return frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": item_code,
			"item_name": item_code,
			"item_group": "All Item Groups",
			"stock_uom": "Nos",
			"is_stock_item": 1,
			"barcodes": [{"barcode": code} for code in barcodes],
		}
	).insert()


class TestDuplicateBarcode(IntegrationTestCase):
	def setUp(self):
		frappe.cache().delete_keys("erpnext:barcode_scan:")
		make_item(ITEMS[0], [SHARED_BARCODE, SINGLE_BARCODE])
		make_item(ITEMS[1], [SHARED_BARCODE])

	def test_items_can_share_barcode(self):
		parents = frappe.get_all("Item Barcode", {"barcode": SHARED_BARCODE}, pluck="parent")
		self.assertCountEqual(parents, ITEMS)

	def test_same_barcode_twice_in_one_item_is_blocked(self):
		item = frappe.get_doc("Item", ITEMS[1])
		item.append("barcodes", {"barcode": SHARED_BARCODE})
		self.assertRaises(frappe.ValidationError, item.save)

	def test_scan_shared_barcode_returns_all_items(self):
		result = scan_barcode(SHARED_BARCODE)
		self.assertCountEqual([row.item_code for row in result["multiple_items"]], ITEMS)

	def test_scan_unique_barcode_returns_single_item(self):
		result = scan_barcode(SINGLE_BARCODE)
		self.assertNotIn("multiple_items", result)
		self.assertEqual(result["item_code"], ITEMS[0])

	def test_resolve_picked_item(self):
		result = resolve_barcode_item(SHARED_BARCODE, ITEMS[1])
		self.assertEqual(result["item_code"], ITEMS[1])
		self.assertEqual(result["barcode"], SHARED_BARCODE)

	def test_resolve_rejects_item_without_barcode(self):
		self.assertRaises(frappe.ValidationError, resolve_barcode_item, SINGLE_BARCODE, ITEMS[1])
