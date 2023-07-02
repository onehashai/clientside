// Copyright (c) 2023, OneHash and contributors
// For license information, please see license.txt

frappe.ui.form.on("Custom domains", {
  refresh: async function (frm) {
    const http_url = `${window.location.protocol}//${window.location.host}/api/method/clientside.clientside.utils.verify_custom_domain`;
    $(".btn[data-fieldname='verify']").text("Verifying domain...");
    $(".btn[data-fieldname='verify']").attr("disabled", true);
    // when  verify button is clicked , call the verify api
    console.log(http_url);
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
      if (message !== "VERIFIED") {
        $(".btn[data-fieldname='verify']").text("Verify");
        $(".btn[data-fieldname='verify']").attr("disabled", false);
      } else {
        $(".btn[data-fieldname='verify']").hide();
      }
    } catch (error) {
      console.log(error);
    }

    $(frm.fields_dict.verify.wrapper).on("click", function () {
      console.log("verify button clicked");

      frappe.call({
        args: {
          new_domain: frm.doc.new_domain,
        },
        method: "clientside.clientside.utils.verify_custom_domain",
        freeze: true,
        freeze_message: "Verifying domain",
        callback: function (r) {
          const { message } = r;
          // message could be VERIFIED,INVALID_DOMAIN_FORMAT,INVALID_RECORD,ALREADY_REGISTERED and INVALID_DOMAIN
          // handle each case and throw a descriptive error in frappe.msgprint
          console.log(message);
          if (message == "VERIFIED") {
            frappe.msgprint("Domain verified successfully");
            $(".btn[data-fieldname='verify']").hide();
            frm.reload_doc();
          } else if (message == "INVALID_DOMAIN_FORMAT") {
            frappe.throw("Please enter a valid domain name");
          } else if (message == "INVALID_RECORD") {
            console.log("invalid record");
            frappe.throw("Please check your DNS records");
          } else if (message == "ALREADY_REGISTERED") {
            frappe.throw("Domain already registered");
          } else if (message == "INVALID_DOMAIN") {
            frappe.throw("Please enter a valid domain name");
          }
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
