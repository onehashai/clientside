class StripeManager {
  constructor(pk_key = "", resgion = "US") {
    this.current_process = "";
    this.stripe = Stripe(pk_key);
    this.current_stripe_price_id = "";
  }
  async upgrade(price_id) {
    this.current_process = "upgrade";
    await fetch(
      "/api/method/clientside.clientside.utils.upgradeOneHashPlan?price_id=" +
        price_id,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    ).then((r) => r.json());
  }
  async purcahse(price_id) {
    const { message } = await fetch(
      "/api/method/clientside.clientside.utils.createNewPurchaseSession?price_id=" +
        price_id,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    ).then((r) => r.json());
    window.location.href = message.url;
  }
}
function switchPlans(price_info) {
  const onTrial = isTrial == "True" ? true : false;

  console.log("switching plans");
  function setPrices(annual) {
    const plans = ["ONEHASH_STARTER", "ONEHASH_PRO", "ONEHASH_PLUS"];
    plans.forEach((plan) => {
      console.log(plan);
      console.log(price_info[plan]);
      const current_plan_button_html = `<button
                class="font-medium text-sm inline-flex items-center justify-center px-3 py-2 border border-transparent rounded leading-5 shadow-sm transition duration-150 ease-in-out border-gray-200 focus:outline-none focus-visible:ring-2 bg-gray-100 text-gray-400 w-full cursor-not-allowed flex items-center"
                disabled
              >
                <svg
                  class="w-3 h-3 flex-shrink-0 fill-current mr-2"
                  viewBox="0 0 12 12"
                >
                  <path
                    d="M10.28 1.28L3.989 7.575 1.695 5.28A1 1 0 00.28 6.695l3 3a1 1 0 001.414 0l7-7A1 1 0 0010.28 1.28z"
                  />
                </svg>
                <span>
                    ${onTrial ? "On Free Trial" : "Current Plan"}  
                </span
                >
              </button>`;
      const subscibe_button_html = `<button
                data-plan="${plan}"
                class="upgrade font-medium text-sm inline-flex items-center justify-center px-3 py-2 border border-transparent rounded leading-5 shadow-sm transition duration-150 ease-in-out bg-indigo-500 focus:outline-none focus-visible:ring-2 hover:bg-indigo-600 text-white w-full"
              >
                ${onTrial && has_subscription ? "Change Plan" : "Subscribe"}
              </button>`;
      const price = price_info[plan][annual ? "yearly" : "monthly"]["price"];
      const price_id =
        price_info[plan][annual ? "yearly" : "monthly"]["price_id"];
      $("#plan[data-plan='" + plan + "']").text(price);
      if (
        price_id == current_price_id &&
        !onTrial &&
        has_subscription == "True"
      ) {
        // create butt
        $("p[data-plan='" + plan + "']").html(current_plan_button_html);
        // create a tag of "free trial" or "current plan" and append it after the .plan-text[data-plan="plan"]
      } else {
        $("p[data-plan='" + plan + "']").html(subscibe_button_html);
        if (onTrial)
          $(".plan-text[data-plan='" + plan + "']").append(
            `<span class="text-xs ml-2 plan-tag">On Trial</span>`
          );
      }
      $("button[data-plan='" + plan + "']").attr("data-price-id", price_id);
      $("#year-label[data-plan='" + plan + "']").text(
        annual ? "/year" : "/month"
      );
    });

    // set button with price_id as current price id

    //       class="font-medium text-sm inline-flex items-center justify-center px-3 py-2 border border-transparent rounded leading-5 shadow-sm transition duration-150 ease-in-out border-gray-200 focus:outline-none focus-visible:ring-2 bg-gray-100 text-gray-400 w-full cursor-not-allowed flex items-center"
    // <svg
    //               class="w-3 h-3 flex-shrink-0 fill-current mr-2"
    //               viewBox="0 0 12 12"
    //             >
    //               <path
    //                 d="M10.28 1.28L3.989 7.575 1.695 5.28A1 1 0 00.28 6.695l3 3a1 1 0 001.414 0l7-7A1 1 0 0010.28 1.28z"
    //               />    <span> Text1 </span>
  }

  setTimeout(() => {
    val = document
      .getElementById("switch-move")
      .classList.contains("switch-move-on");
    console.log(val);
    setPrices(val);
    // disable the current price and set the text to "on free trial" if the user is on trial else "Current Plan"
    // if the user is on trial then set other plans to "subscribe" else "Change plan"
  }, 300);
}

function addEventListeners(stripeManager, price_info) {
  setTimeout(() => {
    console.log("add event listeners", $(".upgrade"));
    $(".upgrade").click(async function () {
      console.log("upgrade");
      showModal();
      var price_id = $(this).data("price-id");
      if (isTrial == "False" && has_subscription == "True") {
        stripeManager.upgrade(price_id);
        return;
      }
      stripeManager.purcahse(price_id);
    });
  }, 500);
}

function realtimeListeners(stripeManager) {
  console.log("realtime listeners", stripeManager);
  frappe.realtime.on("payment_success", ({ message }) => {
    console.log(stripeManager);
    console.log("payment success", message, stripeManager.current_process);
    let current_process = stripeManager.current_process;
    if (current_process == "upgrade") {
      frappe.msgprint({
        title: __("Success"),
        indicator: "green",
        message: __(
          "Your plan has been updated successfully. Please refresh to see the changes."
        ),
      });
    } else if (current_process == "purchase") {
      frappe.msgprint({
        title: __("Success"),
        indicator: "green",
        message: __(
          "Your have subscribed to the selected plan. Please refresh to see the changes."
        ),
      });
    } else {
      frappe.msgprint({
        title: __("Success"),
        indicator: "green",
        message: __("Your payment has been processed successfully."),
      });
    }

    hideModal();
  });

  frappe.realtime.on("payment_failed", ({ message }) => {
    console.log("payment failed", message);
    frappe.msgprint({
      title: __("Payment Failed"),
      indicator: "red",
      message: __(
        "Payment failed. Please try again later or contact OneHash support."
      ),
    });
    hideModal();
  });
  frappe.realtime.on("requires_payment_action", ({ client_secret }) => {
    console.log("requires payment action", client_secret);
    stripeManager.stripe
      .confirmCardPayment(client_secret)
      .then(function (result) {
        // Handle result.error or result.paymentIntent
        console.log(result);
        if (result.error) {
          // show error alert frappe

          frappe.show_alert({
            message: __(result.error.message || "Something went wrong!"),
            indicator: "red",
          });
        } else {
          frappe.show_alert({
            message: __("Payment Successful!"),
            indicator: "green",
          });

          hideModal();
        }
      });
  });
  frappe.realtime.on("upgrade_failed", ({ reason }) => {
    console.log("upgrade failed", reason);
    if (reason == "NO_PAYMENT_METHOD") {
      frappe.msgprint({
        title: __("Payment Method Required"),
        indicator: "red",
        message: __(
          "Please add a default payment method by logging in to your stripe account to upgrade your plan."
        ),
      });
    } else if (reason == "ERROR_IN_PAYMENT") {
      frappe.msgprint({
        title: __("Payment Failed"),
        indicator: "red",
        message: __(
          "Your card has declined. Please try again later or change your default payment method on payment portal."
        ),
      });
    } else if (reason == "PENDING_INVOICE") {
      frappe.msgprint({
        title: __("Payment Failed"),
        indicator: "red",
        message: __(
          "You have a pending invoice. Please pay that first and try again  to upgrade your plan or contact support!"
        ),
      });
    } else if (reason == "TECHNICAL_ERROR") {
      frappe.msgprint({
        title: __("Technical Error"),
        indicator: "red",
        message: __("Something went wrong. Please try again later."),
      });
    }

    hideModal();
  });
}
window.onload = async function () {
  //if in query params "payment_success" then show success alert
  const urlParams = new URLSearchParams(window.location.search);
  const payment_success = urlParams.get("payment_success");
  if (payment_success == "True") {
    frappe.msgprint({
      title: __("Success"),
      indicator: "green",
      message: __("Your plan has been updated successfully."),
    });
  }
  const getUsage = async () => {
    const { message } = await fetch(
      "/api/method/clientside.clientside.utils.getUsage",
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    ).then((r) => r.json());
    return message;
  };
  const usage = await getUsage();
  const stripeManager = new StripeManager(
    usage["stripe_conf"]["publishable_key"]
  );
  $("#payments_portal").click(async function () {
    window.open(usage["stripe_conf"]["customer_portal"], "_blank");
  });
  const country = usage["stripe_conf"]["country"];
  const price_info = usage["stripe_conf"]["pricing"];
  document.querySelectorAll("#price_symbol").forEach((el) => {
    el.innerHTML = country == "IN" ? "₹" : "$";
  });

  console.log(price_info);
  const current_price_id = price_info["ONEHASH_STARTER"]["yearly"]["price_id"];
  stripeManager.current_stripe_price_id = current_price_id;
  switchPlans(price_info);
  addEventListeners(stripeManager, price_info);
  realtimeListeners(stripeManager);
  $("#switch").click(function () {
    switchPlans(price_info);
    $("#switch-move").toggleClass("switch-move-on");
    $("#switch").toggleClass("switch-on-bg");
    addEventListeners(stripeManager, price_info);
  });
  $(".spinner").hide();
  document.getElementById("main").style.visibility = "visible";
};

function showModal() {
  document.querySelector(".modals").style.visibility = "visible";
}
function hideModal() {
  document.querySelector(".modals").style.visibility = "hidden";
}
