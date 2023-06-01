var getQueryString = function (field, url) {
  var href = url ? url : window.location.href;
  var reg = new RegExp("[?&]" + field + "=([^&#]*)", "i");
  var string = reg.exec(href);
  return string ? string[1] : null;
};
let domain = "onehash.store";
window.onload = function () {
  const url = new URL(window.location.href);
  const email = url.searchParams.get("email");
  const password = url.searchParams.get("password").replace(/%23/g, "#");
  const subdomain = url.searchParams.get("domain");
  console.log("email", email);
  console.log("password", password);
  $.ajax({
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
    success: function (data) {
      console.log("data", data);
      if (data.message == "Logged In") {
        console.log("logged in");
        if (window.dev_server) {
          // window.location.href = `http://${subdomain}.localhost:8000/app`;
        } else {
          // window.location.href = `https://${subdomain}.${domain}/app`;
        }
      }
    },
    error: function (data) {
      console.log("error", data);
    },
  });

  //   fetch("/api/method/login", {
  //     method: "POST",
  //     headers: {
  //       "Content-Type": "application/x-www-form-urlencoded",
  //     },
  //     credentials: true,
  //     cache: "no-cache",
  //     body: `usr=${email}&pwd=${password}`,
  //   })
  //     .then((data) => {
  //       console.log("data", data);
  //       return data.json();
  //     })
  //     .then((data) => {
  //       console.log("data", data);
  //       if (data.message == "Logged In") {
  //         console.log("logged in");
  //         // window.location = window.location.hostname + "/app";
  //       } else {
  //         alert("Some error occured. Please try again.");
  //       }
  //     });
};
