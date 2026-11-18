// Item image thumbnails in the Purchase Invoice items table.
// item_images holds image URLs, one per line (set by customizations/item_images.py on save and here on
// item change). The column shows one thumbnail per row; a click opens the full image.
(function () {
	const CHILD = "Purchase Invoice Item";
	const MAX_THUMBS = 1; // one image per row
	const SAFE_URL = /^(https?:\/\/|\/)/i;
	const esc = (s) => frappe.utils.escape_html(s);

	function urls(value) {
		// Grid cells pass the value already HTML-escaped; undo that so each URL is escaped exactly once.
		return frappe.utils
			.unescape_html(cstr(value))
			.split("\n")
			.map((url) => url.trim())
			.filter((url) => SAFE_URL.test(url));
	}

	const DRIVE_ID = /^https:\/\/drive\.google\.com\/file\/d\/([\w-]+)/;
	const BOX = "width:28px;height:28px;border-radius:4px;border:1px solid var(--border-color)";
	// Shown when an image can't load, e.g. a Drive file that isn't shared with the viewer's Google account.
	const PLACEHOLDER = `<span style="${BOX};display:inline-flex;align-items:center;justify-content:center;background:var(--control-bg)">${frappe.utils.icon("image", "sm")}</span>`;

	// Drive files: the image comes from Drive's thumbnail server; the link opens the Drive viewer.
	function thumbnail_src(url) {
		const drive = url.match(DRIVE_ID);
		return drive ? `https://lh3.googleusercontent.com/d/${drive[1]}=w200` : url;
	}

	function thumbnails(value) {
		// Direct images first: they always load, a Drive image only if shared with the viewer
		const list = urls(value).sort((a, b) => DRIVE_ID.test(a) - DRIVE_ID.test(b));
		if (!list.length) return "";
		const thumbs = list.slice(0, MAX_THUMBS).map(
			(url) => `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer" title="${__("Open image")}"
				onclick="event.stopPropagation()" style="display:inline-block;margin-right:3px;line-height:0">
				<img src="${esc(thumbnail_src(url))}" loading="lazy"
					onerror="this.outerHTML=${esc(JSON.stringify(PLACEHOLDER))}"
					style="${BOX};object-fit:cover">
			</a>`
		);
		return `<span style="display:inline-flex;align-items:center;white-space:nowrap">${thumbs.join("")}</span>`;
	}

	frappe.ui.form.on("Purchase Invoice", {
		setup() {
			const df = frappe.meta.get_docfield(CHILD, "item_images");
			if (df) df.formatter = thumbnails;
		},
	});

	frappe.ui.form.on(CHILD, {
		item_code(frm, cdt, cdn) {
			const row = locals[cdt][cdn];
			const item_code = row.item_code;
			if (!item_code) return frappe.model.set_value(cdt, cdn, "item_images", "");
			frappe.call({
				method: "luxury_customization.customizations.item_images.get_item_images",
				args: { item_code },
				callback: (r) => {
					// Ignore a late reply if the item was changed again meanwhile
					if (row.item_code === item_code) frappe.model.set_value(cdt, cdn, "item_images", r.message || "");
				},
			});
		},
	});
})();
