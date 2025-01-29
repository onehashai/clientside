$(document).ready(function () {
  if (frappe.boot.subscription_expired) {
    $(".sticky-top").click(function () {
      if (!window.location.pathname.startsWith("/app/subscription-info")) {
        let dialog = new frappe.ui.Dialog({
          title: __("Subscription Expired"),
          indicator: "red",
          static: true,
          no_close: true,
          fields: [
            {
              fieldtype: "HTML",
              options:
                "<p>Your subscription has expired. Please renew your plan to continue using the platform.</p>",
            },
          ],
          primary_action_label: __("Go to Subscription Page"),
          primary_action() {
            window.location.href = "/app/subscription-info";
          },
        });

        dialog.show();
      }
    });
    $(".main-section").click(function () {
      if (!window.location.pathname.startsWith("/app/subscription-info")) {
        let dialog = new frappe.ui.Dialog({
          title: __("Subscription Expired"),
          indicator: "red",
          static: true,
          no_close: true,
          fields: [
            {
              fieldtype: "HTML",
              options:
                "<p>Your subscription has expired. Please renew your plan to continue using the platform.</p>",
            },
          ],
          primary_action_label: __("Go to Subscription Page"),
          primary_action() {
            window.location.href = "/app/subscription-info";
          },
        });

        dialog.show();
      }
    });
    $("#body").click(function () {
      if (!window.location.pathname.startsWith("/app/subscription-info")) {
        let dialog = new frappe.ui.Dialog({
          title: __("Subscription Expired"),
          indicator: "red",
          static: true,
          no_close: true,
          fields: [
            {
              fieldtype: "HTML",
              options:
                "<p>Your subscription has expired. Please renew your plan to continue using the platform.</p>",
            },
          ],
          primary_action_label: __("Go to Subscription Page"),
          primary_action() {
            window.location.href = "/app/subscription-info";
          },
        });

        dialog.show();
      }
    });
  }
});
