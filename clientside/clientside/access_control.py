import json
from urllib.parse import unquote

import frappe
from frappe import _
from frappe.utils.data import sbool


SCRIPT_CONTROL_DOCTYPES = {"Server Script", "Client Script", "System Console"}
DEFAULT_INTERNAL_DOMAINS = ("onehash.ai",)


def is_script_control_allowed_for_site() -> bool:
	return sbool(frappe.conf.get("clientside_allow_script_control"))


def is_administrator_allowed() -> bool:
	return sbool(frappe.conf.get("clientside_allow_script_control_for_administrator"))


def get_internal_domains() -> tuple[str, ...]:
	domains = frappe.conf.get("clientside_internal_email_domains") or DEFAULT_INTERNAL_DOMAINS
	if isinstance(domains, str):
		domains = [domain.strip() for domain in domains.split(",")]

	return tuple(domain.lower().lstrip("@") for domain in domains if domain)


def is_internal_user(user: str | None = None) -> bool:
	if is_script_control_allowed_for_site():
		return True

	user = (user or frappe.session.user or "").strip().lower()
	if user == "administrator" and is_administrator_allowed():
		return True

	if user in {"", "guest"}:
		return False

	return any(user == domain or user.endswith(f"@{domain}") for domain in get_internal_domains())


def deny_script_control_query_conditions(user: str | None = None, **kwargs) -> str:
	if is_internal_user(user):
		return ""

	return "1 = 0"


def has_script_control_permission(
	doc, ptype: str | None = None, user: str | None = None, **kwargs
) -> bool:
	if getattr(doc, "doctype", None) not in SCRIPT_CONTROL_DOCTYPES:
		return True

	return is_internal_user(user)


def _ensure_internal_user():
	if not is_internal_user():
		frappe.throw(
			_("Access to script management tools is restricted on this site."),
			frappe.PermissionError,
		)


def enforce_script_control_request_access():
	if is_internal_user():
		return

	if _request_targets_script_control():
		_ensure_internal_user()


@frappe.whitelist()
def execute_system_console_code(doc):
	_ensure_internal_user()

	from frappe.desk.doctype.system_console.system_console import execute_code

	return execute_code(doc)


@frappe.whitelist()
def show_system_console_processlist():
	_ensure_internal_user()

	from frappe.desk.doctype.system_console.system_console import show_processlist

	return show_processlist()


def reject_restricted_doctype_payload(doc):
	doctype = _extract_doctype(doc)
	if doctype in SCRIPT_CONTROL_DOCTYPES:
		_ensure_internal_user()


def _extract_doctype(doc):
	if isinstance(doc, str):
		try:
			doc = json.loads(doc)
		except ValueError:
			return None

	if isinstance(doc, dict):
		return doc.get("doctype")

	return getattr(doc, "doctype", None)


def _request_targets_script_control() -> bool:
	form_dict = getattr(frappe.local, "form_dict", None) or {}

	for key in ("doctype", "dt", "reference_doctype"):
		if form_dict.get(key) in SCRIPT_CONTROL_DOCTYPES:
			return True

	for key in ("doc", "docs", "data"):
		if _payload_has_restricted_doctype(form_dict.get(key)):
			return True

	path = unquote(getattr(frappe.request, "path", "") or "")
	return any(f"/{doctype}" in path for doctype in SCRIPT_CONTROL_DOCTYPES)


def _payload_has_restricted_doctype(payload) -> bool:
	if payload is None:
		return False

	if isinstance(payload, str):
		try:
			payload = json.loads(payload)
		except ValueError:
			return False

	if isinstance(payload, dict):
		if payload.get("doctype") in SCRIPT_CONTROL_DOCTYPES:
			return True
		return any(_payload_has_restricted_doctype(value) for value in payload.values())

	if isinstance(payload, list):
		return any(_payload_has_restricted_doctype(value) for value in payload)

	return False
