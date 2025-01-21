// Copyright (c) 2023, OneHash and contributors
// For license information, please see license.txt

frappe.ui.form.on("Custom Domains", {
  refresh: function (frm) {
    const currentDomain = window.location.hostname;
    const htmlContent = `
      <strong>Steps to add a Custom Domain</strong>
      <ol>
        <li>Open your DNS provider settings</li>
        <li>Create a CNAME record with target to your onehash site name</li>
      </ol>
      <strong>For example</strong>, if you want to add <i>www.human.com</i> to your site <i>${currentDomain}</i>
      <ol>
        <li>Open your DNS provider (e.g., GoDaddy)</li>
        <li>Select CNAME as the record type</li>
        <li>Put "www" (your root subdomain) in the "Name" field and <i>${currentDomain}</i> in the "Value" field</li>
        <li>Click the Save button</li>
        <li>Click on the Verify button. The verification might fail for a few minutes due to delay in DNS propagation by your DNS provider</li>
      </ol>
      <p>For more information, contact <a href="mailto:support@onehash.ai">OneHash Support</a>!</p>
    `;

    frm.set_df_property('verification_steps', 'options', htmlContent);
    if (frm.doc.verified === 1) {
      frm.set_df_property('verify','hidden', true);
    }
  },

  verify: function (frm) {
    frappe.call({
        method: "clientside.clientside.doctype.custom_domains.custom_domains.verify_custom_domain",
        args: {
            domain: frm.doc.new_domain || ""
        },
        callback: function (r) {
          if (r.message[0]) {
            frm.set_value('verified', 1);
            frappe.msgprint({
                title: "Success",
                indicator: "green",
                message: "Domain verified successfully!"
            });
            frm.save()
        } else{
            frappe.msgprint({
                title: "Error",
                indicator: "red",
                message: r.message[1]
            });
          }
        }
    });
  }
});