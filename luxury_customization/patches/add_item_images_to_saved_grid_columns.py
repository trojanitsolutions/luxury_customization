import json

import frappe
from frappe.model.utils.user_settings import sync_user_settings

DOCTYPE, CHILD = "Purchase Invoice", "Purchase Invoice Item"
COLUMN = "item_images"


def execute():
	# Saved "Configure Columns" layouts replace in_list_view, so the new Images column never shows for
	# those users. Add it to each saved Purchase Invoice items layout, after Item Code / Item Name.
	sync_user_settings()  # cache can be newer than the table
	rows = frappe.db.sql("select user, data from `__UserSettings` where doctype=%s", (DOCTYPE,), as_dict=True)
	for row in rows:
		data = json.loads(row.data or "{}")
		columns = (data.get("GridView") or {}).get(CHILD)
		if not columns or any(c.get("fieldname") == COLUMN for c in columns):
			continue
		anchor = next(
			(i for name in ("item_name", "item_code") for i, c in enumerate(columns) if c.get("fieldname") == name),
			-1,
		)
		columns.insert(anchor + 1, {"fieldname": COLUMN, "columns": 1})
		frappe.db.sql(
			"update `__UserSettings` set data=%s where user=%s and doctype=%s",
			(json.dumps(data), row.user, DOCTYPE),
		)
		# Drop the cached copy so the next load reads the updated row
		frappe.cache.hdel("_user_settings", f"{DOCTYPE}::{row.user}")
