frappe.ui.form.on('Web Form', {

    onload: function(frm) {
		if (frm.doc.is_embeddable == 1) {
            let msg = `<div class="card mb-3 h-100"><div class="card-body"> <b>Embed URL</b> <br><br><textarea rows="4" cols="50"><iframe frameborder="0" style="height:500px;width:99%;border:none;" src='https://${frappe.boot.sitename}/${frm.doc.route}'></iframe></textarea><br><br> Add this url to your site.</div></div>`
            frm.set_df_property('embed_url', 'options', msg);
        }
	},
	refresh: function(frm) {
        if (frm.doc.is_embeddable == 1) {
            let msg = `<div class="card mb-3 h-100"><div class="card-body"> <b>Embed URL</b> <br><br><textarea rows="4" cols="50"><iframe frameborder="0" style="height:500px;width:99%;border:none;" src='https://${frappe.boot.sitename}/${frm.doc.route}'></iframe></textarea><br><br> Add this url to your site.</div></div>`
            frm.set_df_property('embed_url', 'options', msg);
        }
    },

	is_embeddable: function (frm) {
        if (frm.doc.is_embeddable == 1) {
            
            let msg = `<div class="card mb-3 h-100"><div class="card-body"> <b>Embed URL</b> <br><br><textarea rows="4" cols="50"><iframe frameborder="0" style="height:500px;width:99%;border:none;" src='https://${frappe.boot.sitename}/${frm.doc.route}'></iframe></textarea><br><br> Add this url to your site.</div></div>`
            frm.set_df_property('embed_url', 'options', msg);
            frm.dirty()
        }
        if(frm.doc.is_embeddable == 0){
            frm.dirty()
        }
		
	}
});
