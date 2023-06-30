frappe.pages["usage-info"].on_page_load = async function (wrapper) {
  var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Usage Info"),
    single_column: true,
  });
  $(frappe.render_template("usage_info")).appendTo(
    page.body.addClass("no-border")
  );
  const r = await fetch("/api/method/clientside.clientside.utils.getUsage");
  const { message } = await r.json();
  console.log(message);
  init(message);
};
function fillEmailUsage(usage_info) {
  const percent = (usage_info.emails / usage_info.email_limit) * 100;
  console.log("email perc", percent);
  setPercentage("emails", percent, usage_info.emails, usage_info.email_limit);
}

async function addNumberOfDays(usage_info) {
  if (usage_info.days_left == 1) {
    $("#days").html(usage_info.days_left + " day left");
  } else {
    $("#days").html(usage_info.days_left + " days left");
  }
  const percent = (usage_info.days_left / usage_info.total_days) * 100;
  drawProgress(percent);
}
function init(usage_info) {
  addNumberOfDays(usage_info);
  filUserUsage(usage_info);
  fillEmailUsage(usage_info);
  fillStorageUsage(usage_info);
  $("#delete-site").click(async function () {
    frappe.warn(
      "Are you sure you want to proceed?",
      " This action is not reversible.",
      () => {
        // action to perform if Continue is selected
        frappe.call({
          method: "clientside.clientside.utils.delete_site_from_server",

          freeze_message: __("Deleting site"),
          freeze: true,
          error: function () {
            frappe.msgprint("Site has been deleted successfully");
            // refresh page
            window.location.reload();
          },
        });
      },
      "Continue",
      true
    );
  });
}
function filUserUsage(usage_info) {
  const percent = (usage_info.users / usage_info.user_limit) * 100;
  console.log("user perc", percent);
  setPercentage("user", percent, usage_info.users, usage_info.user_limit);
}
function getColor(percent) {
  console.log("get color", percent);
  if (percent < 30) {
    return "danger";
  }
  if (percent >= 30 && percent < 60) {
    return "warn";
  }
  if (percent > 60) {
    return "success";
  }
}

function drawProgress(percent) {
  // danger for less than 30 , warning for less than 60, success for more than 60
  const color = getColor(percent);
  $(".fill").addClass(color);
  var forEach = function (array, callback, scope) {
    for (var i = 0; i < array.length; i++) {
      callback.call(scope, i, array[i]);
    }
  };
  var max = -219.99078369140625;
  forEach(document.querySelectorAll(".iprogress"), function (index, value) {
    console.log(value);
    value
      .querySelector(".fill")
      .setAttribute(
        "style",
        "stroke-dashoffset: " + ((100 - percent) / 100) * max
      );
  });
}
function fillProgressBar(percentage, tag, addColor = true) {
  console.log("fill progress bar", percentage, tag);
  console.log(
    document.querySelector(".progress-bar[data-name=storage-backup]")
  );
  if (addColor)
    document
      .querySelector(".progress-bar[data-name='" + tag + "']")
      .classList.add(getColor(percentage));
  document.querySelector(".progress-bar[data-name='" + tag + "']").style.width =
    percentage + "%";
}

function fillStorageUsage(usage_info) {
  // site's total storage = backup + site files + db
  // we have total limit of storage_limit
  // we convert all to GB
  // we then calculate the percentage of each and fill the progress bar
  const total_storage = Number(convertToG(usage_info.storage_limit));
  const backup = convertToG(usage_info.storage.backup_size);
  const site_files = convertToG(usage_info.storage.site_size) - backup;
  const db = convertToG(usage_info.storage.database_size);
  console.log("total storage", total_storage);
  console.log("backup", backup);
  console.log("site files", site_files);
  console.log("db", db);
  const used_storage = Number(backup) + Number(site_files) + Number(db);

  console.log("used storage", used_storage);

  const used_percentage = (used_storage / total_storage) * 100;
  setPercentage(
    "storage",
    used_percentage.toFixed(2),
    used_storage.toFixed(2),
    total_storage.toFixed(2)
  );
}

function convertToG(strinWithPrefix) {
  // eg : 0B, 68.3M,860K
  console.log("convert to g", strinWithPrefix);
  const prefix = strinWithPrefix.slice(-1);
  const number = strinWithPrefix.slice(0, -1);

  if (prefix == "B") {
    return number;
  }
  if (prefix == "K") {
    return number / 1000000;
  }
  if (prefix == "M") {
    return number / 1000;
  }
  if (prefix == "G") {
    return number + "";
  }
}

function setPercentage(name, percentage, used, total) {
  const getText = function (name, used, total) {
    if (name === "user") {
      return used + " / " + total + " Created";
    }
    if (name === "storage") {
      return used + " / " + total + " GB";
    }
    if (name === "emails") {
      return used + " / " + total + " Sent";
    }
  };
  console.log("set percentage", name, percentage);
  const progressEl = document.getElementById("progress-" + name);
  const percentageEl = document.getElementById("progress-" + name + "-perc");
  console.log(progressEl, percentageEl);

  progressEl.classList.add(getColor(100 - percentage));
  percentageEl.classList.add(getColor(100 - percentage));
  progressEl.style.width = percentage + "%";
  percentageEl.innerText = getText(name, used, total);
  percentageEl.style.left = percentage + "%";
}

const addCustomDomain = async function () {
  const { site } = await fetch(
    "/api/method/clientside.clientside.doctype.saas_sites.saas_sites.add_custom_domain"
  ).then((r) => r.json());
  console.log(site);
};

const verifyCustomDomainPoll = async function (retries = 10) {
  const { status } = await fetch(
    "/api/method/clientside.clientside.doctype.saas_sites.saas_sites.verify_custom_domain"
  ).then((r) => r.json());
  console.log(status);
  if (status == "pending" && retries > 0) {
    setTimeout(() => {
      verifyCustomDomainPoll(retries - 1);
    }, 5000);
  } else {
    if (status == "verified") {
      frappe.show_alert({
        message: __("Domain verified successfully"),
        indicator: "green",
      });
    } else {
      frappe.show_alert({
        message: __("Domain verification failed"),
        indicator: "red",
      });
    }
  }
};
