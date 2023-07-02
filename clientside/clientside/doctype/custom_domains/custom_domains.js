// Copyright (c) 2023, OneHash and contributors
// For license information, please see license.txt

frappe.ui.form.on("Custom domains", {
  refresh: async function (frm) {
    const http_url = `http://${
      frm.doc.new_domain +
      (window.location.port ? ":" + window.location.port : "")
    }/api/method/clientside.clientside.utils.verify_custom_domain`;
    $(frm.fields_dict.verify.wrapper).hide();
    // when  verify button is clicked , call the verify api
    console.log(frm.doc);
    let isVerified = false;
    try {
      console.log(http_url);
      const { message } = await $.ajax({
        url: http_url,
        type: "GET",
        dataType: "json",
        data: {
          new_domain: frm.doc.new_domain,
        },
      });
      console.log("CNAME record verified");
      isVerified = true;
    } catch (error) {
      console.log(error);
    }

    if (!isVerified) {
      $(frm.fields_dict.verify.wrapper).show();
    }
    $(frm.fields_dict.verify.wrapper).on("click", function () {
      console.log("verify button clicked");

      frappe.call({
        args: {
          new_domain: frm.doc.new_domain,
        },
        url: http_url,
        freeze: true,
        freeze_message: "Verifying domain",
        success: function (r) {
          console.log(r);

          frappe.msgprint("Domain verified successfully");
          // refresh the page
          window.location.reload();
        },
        error: function (r) {
          console.log(r);
          frappe.msgprint("Error verifying domain");
        },
      });
    });
    setCSS();
  },
});
function setCSS() {
  // add btn-danger class to remove button
  $(".btn[data-fieldname='verify']").addClass("btn-primary");
}
