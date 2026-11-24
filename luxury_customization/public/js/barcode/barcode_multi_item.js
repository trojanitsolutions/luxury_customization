// When one barcode is shared by several items (for example colors),
// ask the user which item to add instead of picking the first one.
frappe.provide("luxury_customization.barcode");

luxury_customization.barcode.patch_scanner = function () {
	const Scanner = window.erpnext && erpnext.utils && erpnext.utils.BarcodeScanner;
	if (!Scanner || Scanner.prototype.__multi_item_patched) return;

	const original_scan_api_call = Scanner.prototype.scan_api_call;

	Scanner.prototype.scan_api_call = function (input, callback) {
		original_scan_api_call.call(this, input, (r) => {
			const items = r && r.message && r.message.multiple_items;
			if (!items) return callback(r);

			luxury_customization.barcode.pick_item(input, items, this.frm, callback);
		});
	};
	Scanner.prototype.__multi_item_patched = true;
};

luxury_customization.barcode.pick_item = function (barcode, items, frm, callback) {
	let picked = false;

	const rows = items
		.map(
			(item, idx) => `
			<button class="btn btn-default btn-block text-left lux-barcode-pick" data-idx="${idx}">
				<b>${frappe.utils.escape_html(item.item_code)}</b>
				<span class="text-muted">${frappe.utils.escape_html(item.item_name || "")}</span>
			</button>`
		)
		.join("");

	const dialog = new frappe.ui.Dialog({
		title: __("Barcode {0} matches {1} items. Select one.", [
			frappe.utils.escape_html(barcode),
			items.length,
		]),
		fields: [{ fieldtype: "HTML", fieldname: "items_html", options: rows }],
	});

	dialog.$wrapper.on("click", ".lux-barcode-pick", function () {
		const item = items[$(this).data("idx")];
		picked = true;
		dialog.hide();

		frappe
			.call({
				method: "luxury_customization.barcode.api.resolve_barcode_item",
				args: {
					barcode: barcode,
					item_code: item.item_code,
					ctx: { set_warehouse: frm.doc.set_warehouse, company: frm.doc.company },
				},
			})
			.then((res) => callback(res));
	});

	dialog.onhide = () => {
		if (!picked) callback({ message: {} });
	};

	dialog.show();
};

$(document).ready(() => luxury_customization.barcode.patch_scanner());
