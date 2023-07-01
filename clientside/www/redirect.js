var getQueryString = function (field, url) {
  var href = url ? url : window.location.href;
  var reg = new RegExp("[?&]" + field + "=([^&#]*)", "i");
  var string = reg.exec(href);
  return string ? string[1] : null;
};
let domain = "." + window.location.hostname.split(".").splice(1, 2).join(".");
if (window.location.port) {
  domain += ":" + window.location.port;
}
const http_protocol = window.location.protocol;
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
  password,
  country
) {
  const country_name = (
    await (
      await fetch("https://restcountries.com/v3.1/alpha/" + country)
    ).json()
  )[0]["name"]["common"];
  console.log(country_name);
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
        country: country_name,
      },
      async: true,
    })
    .then((r) => {
      console.log(r);
      if (r.message.status == "OK") {
        console.log("User created", email);
        login(email, password).then(() => {
          redirect();
        });
      } else {
        console.log(r.message);
        if (r.message == errorMessages.EMAIL_ALREADY_REGISTERED) {
          console.log("User already exists, logging in");
          login(email, password).then(() => {
            redirect();
          });
        } else if (
          r.message == errorMessages.EMAIL_ALREADY_REGISTERED_BUT_DISABLED
        ) {
          console.log("User already exists, logging in");
          login(email, password).then(() => {
            redirect();
          });
        } else {
          frappe.msgprint(r.message);
        }
      }
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
  let password = url.searchParams.get("password") || "admin";
  if (password == null) {
    password = "admin";
  }

  const firstname = url.searchParams.get("firstname") || "Test";
  const lastname = url.searchParams.get("lastname") || "User";
  const companyname = url.searchParams.get("companyname") || "OneHash";
  const country = url.searchParams.get("country") || "India";
  const decryptedPassword = CryptoJS.enc.Base64.parse(password).toString(
    CryptoJS.enc.Utf8
  );
  const createUser = url.searchParams.get("createUser") || false;
  console.log("decryptedPassword", decryptedPassword);
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
    // just login and redirect
    await login(email, password);
    redirect();
  }
}
