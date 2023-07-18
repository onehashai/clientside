// clear cache
async function checkIfUserHasActiveSubsciprion() {
  let url = new URL(window.location.href);
  const isOnboard = url.searchParams.get("onboard");
  let method = "/api/method/clientside.stripe.hasActiveSubscription";
  if (true) {
    method += "?invalidate_cache=true";
    // frappe.ui.toolbar.clear_cache();
    // clear cache
    // refresh page
  }

  const hasActiveSubscription = await fetch(method, {
    method: "GET",
  }).then((r) => r.json());
  if (hasActiveSubscription.message) {
    return true;
  }
  return false;
}
async function checkIfUserHasRoleToManageOnehashPayments() {
  const hasRoleToManageOnehashPayments = await fetch(
    "/api/method/clientside.clientside.utils.hasRoleToManageOnehashPayments"
  ).then((r) => r.json());
  if (hasRoleToManageOnehashPayments.message) {
    return true;
  }
  return false;
}
// plan page is accessible to only logged in users
// on each login , we check if the user has an active subscription and update the cache
// and return if this user has the role to manage onehash payments
// if the user has the role to manage onehash payments, we show the plan page after login
// if the user does not have the role to manage onehash payments, we redirect the user to the " Please contact site administrator to upgrade your plan" page
function init() {
  const url = new URL(window.location.href);
  const isOnboard = url.searchParams.get("oneboard");

  checkIfUserHasActiveSubsciprion().then((hasActiveSubscription) => {
    console.log("hasActiveSubscription", hasActiveSubscription);
    if (!hasActiveSubscription) {
      checkIfUserHasRoleToManageOnehashPayments().then(
        (hasRoleToManageOnehashPayments) => {
          console.log(
            "hasRoleToManageOnehashPayments",
            hasRoleToManageOnehashPayments
          );
          if (hasRoleToManageOnehashPayments) {
            // show the plan page
            console.log("show the plan page");
            // window.location.href = "/plans";
          } else {
            // redirect to "Please contact site administrator to upgrade your plan" page
            console.log(
              "redirect to Please contact site administrator to upgrade your plan page"
            );
            // window.location.href = "/no-plan";
          }
        }
      );
    } else {
      console.log("doing nothing");
    }
  });
}
init();
