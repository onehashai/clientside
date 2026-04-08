const LINK_MAP = {
  "https://docs.erpnext.com//docs/user/manual/en/setting-up/articles/delete-submitted-document":
    "https://chat.onehash.ai/hc/onehash-help-center/articles/1701752414-delete-submitted-document",
  "https://docs.erpnext.com/docs/v14/user/manual/en/regional/india/generating_e_invoice#what-if-we-generate-e-waybill-before-the-e-invoice":
    "https://chat.onehash.ai/hc/onehash-help-center/articles/1701664426-e_invoicing-under-gst#generating-irn",
  "https://docs.erpnext.com/docs/user/manual/en/regional/india/gst-setup":
    "https://chat.onehash.ai/hc/onehash-help-center/articles/1701753695-gst-setup",
};

const DOCS_FALLBACK = "https://chat.onehash.ai/hc/onehash-help-center/en/";
const HOME_FALLBACK = "https://onehash.ai";
const GITHUB_FALLBACK = "https://github.com/onehashai";

function whitelabelText(str) {
  if (typeof str !== "string") return str;
  return str
    .replace(/\bERPNext\b/gi, "OneHash")
    .replace(/\bFrappe\b/gi, "OneHash");
}

function whitelabelLink(url) {
  if (!url) return url;

  if (LINK_MAP[url]) return LINK_MAP[url];

  if (/https?:\/\/docs\.(erpnext|frappe)\./i.test(url)) return DOCS_FALLBACK;

  if (/https?:\/\/github\.com\/(erpnext|frappe)\//i.test(url))
    return GITHUB_FALLBACK;

  if (/https?:\/\/[^/]*(erpnext|frappe)[^/]*/i.test(url)) return HOME_FALLBACK;

  return url;
}

function whitelabelHTML(html) {
  if (typeof html !== "string") return html;

  html = html.replace(
    /(href|src)=(["'])([^"']+)\2/gi,
    (match, attr, quote, url) => {
      return `${attr}=${quote}${whitelabelLink(url)}${quote}`;
    },
  );

  html = html.replace(/(?<=>|^)([^<]+)/g, (match) => whitelabelText(match));

  return html;
}

function whitelabelMessage(msg) {
  if (typeof msg === "string") {
    return whitelabelHTML(msg);
  }
  if (Array.isArray(msg)) {
    return msg.map((item) => {
      if (typeof item === "string") {
        try {
          const parsed = JSON.parse(item);
          return JSON.stringify(whitelabelData(parsed));
        } catch {
          return whitelabelHTML(item);
        }
      }
      return typeof item === "object" ? whitelabelData(item) : item;
    });
  }
  return msg;
}

function whitelabelData(data) {
  if (!data) return data;

  if (data.title) {
    data.title = whitelabelText(data.title);
  }

  if (data.message !== undefined) {
    data.message = whitelabelMessage(data.message);
  }

  return data;
}

const _msgprint = frappe.msgprint;

frappe.msgprint = function (msg, title, is_minimizable) {
  if (!msg) return;

  let data;

  if ($.isPlainObject(msg)) {
    data = msg;
  } else if (typeof msg === "string" && msg.trimStart().startsWith("{")) {
    try {
      data = JSON.parse(msg);
    } catch {
      data = { message: msg, title: title };
    }
  } else {
    data = { message: msg, title: title };
  }

  data = whitelabelData(data);

  _msgprint(data, data.title, is_minimizable);
};
