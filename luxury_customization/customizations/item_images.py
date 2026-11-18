"""Item image thumbnails on Purchase Invoice item rows.

`item_images` keeps the image URLs of the row's Item (Item.image first, then every image file attached
to the Item), one per line. The client renders them as thumbnails in the items table.
Google Drive links are stored as "https://drive.google.com/file/d/<id>/view"; the client builds the
thumbnail from the file id and falls back to a placeholder when Drive does not serve it (file not shared).
"""

import re

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

ITEM_DOCTYPES = ["Purchase Invoice Item"]
FIELDS = [
	{
		"fieldname": "item_images",
		"fieldtype": "Small Text",
		"label": "Images",
		"insert_after": "item_name",
		"read_only": 1,
		"in_list_view": 1,
		"columns": 1,
		"print_hide": 1,
		"no_copy": 1,
	},
]
FIELDNAMES = [f["fieldname"] for f in FIELDS]

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".avif")
DRIVE_FILE = re.compile(
	r"^https://(?:drive|docs)\.google\.com/(?:file/(?:u/\d+/)?d/|open\?id=|uc\?(?:export=\w+&)?id=|thumbnail\?id=)([\w-]+)"
)


def create_custom_fields():
	for doctype in ITEM_DOCTYPES:
		for field in FIELDS:
			if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]}):
				create_custom_field(doctype, field)
		frappe.clear_cache(doctype=doctype)


def delete_custom_fields():
	for doctype in ITEM_DOCTYPES:
		for fieldname in FIELDNAMES:
			frappe.delete_doc("Custom Field", f"{doctype}-{fieldname}", ignore_missing=True)
		frappe.clear_cache(doctype=doctype)


def image_url(url):
	# Thumbnail-able URL for an attachment, or None when it is not an image.
	url = (url or "").strip()
	drive = DRIVE_FILE.match(url)
	if drive:
		return f"https://drive.google.com/file/d/{drive.group(1)}/view"
	if url.split("?")[0].lower().endswith(IMAGE_EXTENSIONS):
		return url
	return None


def images_by_item(item_codes):
	# {item_code: [url, ...]}: Item.image first, then the Item's attachments in upload order, no duplicates.
	item_codes = list({code for code in item_codes if code})
	if not item_codes:
		return {}
	urls = {code: [] for code in item_codes}
	for code, image in frappe.get_all(
		"Item", filters={"name": ("in", item_codes)}, fields=["name", "image"], as_list=True
	):
		urls[code].append(image)
	for code, file_url in frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Item", "attached_to_name": ("in", item_codes), "is_folder": 0},
		fields=["attached_to_name", "file_url"],
		order_by="creation asc",
		as_list=True,
	):
		urls[code].append(file_url)
	return {code: list(dict.fromkeys(filter(None, map(image_url, found)))) for code, found in urls.items()}


@frappe.whitelist()
def get_item_images(item_code):
	frappe.has_permission("Item", "read", item_code, throw=True)
	return "\n".join(images_by_item([item_code]).get(item_code, []))


def set_item_images(doc):
	# Draft only: a submitted invoice keeps the images it was submitted with.
	if doc.docstatus != 0:
		return
	images = images_by_item(row.item_code for row in doc.items)
	for row in doc.items:
		row.item_images = "\n".join(images.get(row.item_code, []))
