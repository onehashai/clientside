var getQueryString = function (field, url) {
  var href = url ? url : window.location.href;
  var reg = new RegExp("[?&]" + field + "=([^&#]*)", "i");
  var string = reg.exec(href);
  return string ? string[1] : null;
};

async function logout() {
  await $.ajax({
    url: "/api/method/logout",
    type: "POST",
    crossDomain: true,
    xhrFields: {
      withCredentials: true,
    },
    dataType: "json",
    success: function (data) {
      if (data.message == "ok") {
        console.log("User logged out");
      } else {
        frappe.msgprint("Error logging out");
      }
    },
  });
}
async function createNewUser(
  email,
  firstname,
  lastname,
  companyname,
  password,
  country
) {
  frappe
    .call({
      method: "clientside.clientside.utils.createUserOnTargetSite",
      args: {
        email: email,
        firstname: firstname,
        lastname: lastname,
        companyname: companyname,
        password: password,
        company_name: companyname,
        country: country,
      },
      async: true,
    })
    .then((r) => {
      if (r.message.status == "OK") {
        login(email, password).then(() => {
          redirect();
        });
      } else {
        frappe.msgprint(r.message);
      }
    });
}
async function redirect() {
  return;
  console.log("redirecting to the new site..");
  const url =
    window.location.protocol +
    "//" +
    window.location.host +
    "/app?onboard=true";
  const poll_url =
    "/api/method/clientside.stripe.hasActiveSubscription?invalidate_cache=true";
  // poll until the cache is updated
  const subPoll = await fetch(poll_url, {
    method: "GET",
  }).then((r) => r.json());
  if (subPoll.message) {
    window.location.href = url;
  } else {
    setTimeout(() => {
      redirect();
    }, 2000);
  }
}

async function login(email, password) {
  console.log("trying to login", email, password);
  try {
    await $.ajax({
      url: "/api/method/login",
      type: "POST",
      data: {
        usr: email,
        pwd: password,
      },
      crossDomain: true,
      xhrFields: {
        withCredentials: true,
      },
      dataType: "json",
    });
  } catch (error) {
    console.log(error);
    frappe.msgprint("Some Internal error , please try again later");
  }
}
window.onload = function () {
  init();
};
async function init() {
  const url = new URL(window.location.href);
  const email =
    url.searchParams.get("email") ||
    Math.random().toString(36).substring(7) + "@onehash.ai";
  let password = url.searchParams.get("utm_id") || "admin";
  if (password == null) {
    password = "admin";
  }

  const firstname = url.searchParams.get("firstname") || "Test";
  const lastname = url.searchParams.get("lastname") || "User";
  const companyname = url.searchParams.get("companyname") || "OneHash";
  const country = url.searchParams.get("country") || "India";
  console.log(password);
  const decryptedPassword = CryptoJS.enc.Base64.parse(password).toString(
    CryptoJS.enc.Utf8
  );
  console.log(decryptedPassword);
  const createUser = url.searchParams.get("createUser") || false;
  password = decryptedPassword;
  password = password.replaceAll(/%23/g, "#");
  if (createUser) {
    await login("Administrator", password);
    await createNewUser(
      email,
      firstname,
      lastname,
      companyname,
      password,
      country
    );
  } else {
    console.log("logging in");
    await login(email, password);
    redirect();
  }
}
