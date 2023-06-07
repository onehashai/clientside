var getQueryString = function (field, url) {
  var href = url ? url : window.location.href;
  var reg = new RegExp("[?&]" + field + "=([^&#]*)", "i");
  var string = reg.exec(href);
  return string ? string[1] : null;
};
if (window.dev_server) {
  domain = ".localhost:8000";
} else {
  domain = ".onehash.store";
}
const errorMessages = {
  EMAIL_ALREADY_REGISTERED: "Email already registered",
  INVALID_EMAIL_FORMAT: "Invalid email format",
  PASSWORD_NOT_STRONG: "Password not strong",
  FIRST_NAME_NOT_PROVIDED: "First name not provided",
  LAST_NAME_NOT_PROVIDED: "Last name not provided",
  EMAIL_ALREADY_REGISTERED: "Email already registered",
  EMAIL_ALREADY_REGISTERED_BUT_DISABLED:
    "Email already registered but disabled",
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
  password
) {
  await frappe.call({
    method: "clientside.clientside.utils.create_new_user",
    args: {
      email: email,
      firstname: firstname,
      lastname: lastname,
      companyname: companyname,
      password: password,
    },
    callback: async function (r) {
      if (r.message === "OK") {
        console.log("User created", email);
        await login(email, password);
        redirect();
      } else {
        frappe.msgprint(errorMessages[r.message]);
      }
    },
  });
}
function redirect() {
  console.log("redirecting to the new site");
  window.location.href = `http://${
    window.location.hostname.split(".")[0]
  }${domain}/app`;
}

async function login(email, password) {
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

  console.log("User logged in", email);
}
window.onload = function () {
  init();
};
async function test() {
  init();
}
async function init() {
  const url = new URL(window.location.href);
  const email =
    url.searchParams.get("email") ||
    Math.random().toString(36).substring(7) + "@onehash.ai";
  let password = url.searchParams.get("password");
  if (password == null) {
    password = "admin";
  }
  password = password.replaceAll(/%23/g, "#");
  const firstname = url.searchParams.get("firstname") || "Test";
  const lastname = url.searchParams.get("lastname") || "User";
  const companyname = url.searchParams.get("companyname") || "OneHash";
  await login("Administrator", password);
  await createNewUser(email, firstname, lastname, companyname, password);
}
