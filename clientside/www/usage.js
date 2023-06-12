window.onload = async function () {
  frappe.call({
    method: "clientside.clientside.utils.getUsage",
    async: true,
    callback: function (r) {
      console.log(r.message);
      Object.keys(r.message.storage).forEach((key) => {
        r.message["storage"][key] = convertToMB(r.message.storage[key]);
      });
      console.log(r.message);
    },
  });
};
function convertToMB(stringSize) {
  prefix = stringSize.slice(-1);
  if (prefix === "B") {
    return parseInt(stringSize.slice(0, -1)) / 1000000;
  } else if (prefix === "K") {
    return parseInt(stringSize.slice(0, -1)) / 1000;
  } else if (prefix === "M") {
    return parseInt(stringSize.slice(0, -1));
  } else if (prefix === "G") {
    return parseInt(stringSize.slice(0, -1)) * 1000;
  } else if (prefix === "T") {
    return parseInt(stringSize.slice(0, -1)) * 1000000;
  } else {
    return "Error";
  }
}
