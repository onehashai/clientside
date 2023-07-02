frappe.listview_settings["Custom domains"] = {
  add_fields: ["short_description", "verified"],
  get_indicator: function (doc) {
    console.log("doc", doc);
    console.log("doc.verified", doc.verified);
    if (doc.verified === "1") {
      return [__("Verified"), "green", "new_domain,=," + doc.new_domain];
    }
    return [__("Not Verified"), "red", "new_domain,=," + doc.new_domain];
  },
};
