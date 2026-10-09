import hashlib
import hmac
import json
import os
import re
import secrets
import tempfile
import time
from urllib.parse import urlparse

import frappe
from frappe.utils import cint
from frappe.utils.synchronization import filelock


PROTOCOL_VERSION = 1
MAX_CLOCK_SKEW_SECONDS = 300
PREVIOUS_KEY_TTL_SECONDS = 86400
MANAGEMENT_METHODS = {
	"/api/method/clientside.enterprise_management.reconcile",
	"/api/method/clientside.enterprise_management.rotate_secret",
}
MANAGED_CONFIG_KEYS = {
	"customer_id",
	"invoice_due_date",
	"max_email",
	"max_storage",
	"min_license",
	"plan_name",
	"price_id",
	"product_id",
	"saas_site_disabled",
	"site_expiry_date",
	"skip_subscription_expiry",
	"stripe_subscription_event_created",
	"subscription_ends_on",
	"subscription_expiry_grace_days",
	"subscription_id",
	"subscription_quantity",
	"subscription_starts_on",
	"subscription_status",
}
INTEGER_CONFIG_KEYS = {
	"max_email",
	"max_storage",
	"min_license",
	"saas_site_disabled",
	"skip_subscription_expiry",
	"stripe_subscription_event_created",
	"subscription_expiry_grace_days",
	"subscription_quantity",
}
KEY_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{8,128}$")


def _site_config_path():
	return frappe.get_site_path("site_config.json")


def _write_site_config(updates):
	"""Write all updates under one lock and replace the config atomically."""
	config_path = _site_config_path()
	with filelock("site_config"):
		with open(config_path) as config_file:
			config = json.load(config_file)

		for key, value in updates.items():
			if value is None:
				config.pop(key, None)
			else:
				config[key] = value

		config_dir = os.path.dirname(config_path)
		fd, temporary_path = tempfile.mkstemp(prefix=".site_config.", dir=config_dir)
		try:
			with os.fdopen(fd, "w") as temporary_file:
				json.dump(config, temporary_file, indent=1, sort_keys=True)
				temporary_file.flush()
				os.fsync(temporary_file.fileno())
			os.chmod(temporary_path, os.stat(config_path).st_mode)
			os.replace(temporary_path, config_path)
		finally:
			if os.path.exists(temporary_path):
				os.unlink(temporary_path)

	for key, value in updates.items():
		if value is None:
			frappe.local.conf.pop(key, None)
		else:
			frappe.local.conf[key] = value


def _validate_key(key_id, secret):
	if not KEY_ID_PATTERN.fullmatch(key_id or ""):
		frappe.throw("Invalid enterprise management key id")
	if not isinstance(secret, str) or len(secret) < 32:
		frappe.throw("Enterprise management secret must contain at least 32 characters")


def _normalise_management_url(url):
	if not url:
		return None
	parsed = urlparse(url)
	if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
		frappe.throw("The Bettersaas URL must be an HTTPS origin")
	return f"https://{parsed.netloc}"


@frappe.whitelist()
def bootstrap(key_id, admin_url=None, force=0):
	"""One-time setup authenticated by the site's existing Frappe administrator."""
	if frappe.session.user != "Administrator":
		frappe.only_for("System Manager")

	secret = frappe.request.headers.get("X-Bettersaas-Bootstrap-Secret")
	_validate_key(key_id, secret)
	existing_key_id = frappe.conf.get("enterprise_management_key_id")
	existing_secret = frappe.conf.get("enterprise_management_secret")
	if (
		existing_secret
		and (existing_key_id != key_id or existing_secret != secret)
		and not cint(force)
	):
		frappe.throw("Enterprise management is already provisioned; rotate its secret instead")

	updates = {
		"enterprise": 1,
		"enterprise_management_key_id": key_id,
		"enterprise_management_secret": secret,
		"enterprise_management_previous_key_id": None,
		"enterprise_management_previous_secret": None,
		"enterprise_management_previous_expires_at": None,
		"enterprise_management_last_revision": cint(
			frappe.conf.get("enterprise_management_last_revision")
		),
		"saas_site_disabled": cint(frappe.conf.get("saas_site_disabled")),
	}
	management_url = _normalise_management_url(admin_url)
	if management_url:
		updates["admin_url"] = management_url.removeprefix("https://")
	_write_site_config(updates)
	return {
		"protocol_version": PROTOCOL_VERSION,
		"site": frappe.local.site,
		"key_id": key_id,
	}


def _get_request_body():
	body = frappe.request.get_data(cache=True) or b"{}"
	try:
		payload = json.loads(body)
	except (TypeError, ValueError):
		raise frappe.ValidationError("Invalid JSON request body")
	if not isinstance(payload, dict):
		raise frappe.ValidationError("Request body must be a JSON object")
	return body, payload


def _candidate_secrets(key_id, now):
	if key_id == frappe.conf.get("enterprise_management_key_id"):
		return [frappe.conf.get("enterprise_management_secret")]
	if (
		key_id == frappe.conf.get("enterprise_management_previous_key_id")
		and cint(frappe.conf.get("enterprise_management_previous_expires_at")) >= now
	):
		return [frappe.conf.get("enterprise_management_previous_secret")]
	return []


def _claim_nonce(site, key_id, nonce):
	if not nonce or len(nonce) > 128:
		raise frappe.AuthenticationError("Invalid management request nonce")
	cache = frappe.cache()
	redis_key = cache.make_key(
		f"enterprise-management-nonce:{site}:{key_id}:{nonce}", shared=True
	)
	if not cache.set(redis_key, b"1", nx=True, ex=MAX_CLOCK_SKEW_SECONDS):
		raise frappe.AuthenticationError("Management request was already used")


def _authenticate_request(body):
	headers = frappe.request.headers
	key_id = headers.get("X-Bettersaas-Key-Id", "")
	nonce = headers.get("X-Bettersaas-Nonce", "")
	site = headers.get("X-Bettersaas-Site", "")
	signature = headers.get("X-Bettersaas-Signature", "")
	try:
		timestamp = int(headers.get("X-Bettersaas-Timestamp", ""))
	except (TypeError, ValueError):
		raise frappe.AuthenticationError("Invalid management request timestamp")

	now = int(time.time())
	if abs(now - timestamp) > MAX_CLOCK_SKEW_SECONDS:
		raise frappe.AuthenticationError("Management request timestamp is outside the allowed window")
	if site != frappe.local.site:
		raise frappe.AuthenticationError("Management request site does not match")

	canonical = "\n".join(
		(
			frappe.request.method.upper(),
			frappe.request.path,
			str(timestamp),
			nonce,
			hashlib.sha256(body).hexdigest(),
		)
	).encode()
	provided = signature.removeprefix("sha256=")
	valid = any(
		secret
		and hmac.compare_digest(
			hmac.new(secret.encode(), canonical, hashlib.sha256).hexdigest(), provided
		)
		for secret in _candidate_secrets(key_id, now)
	)
	if not valid:
		raise frappe.AuthenticationError("Invalid enterprise management signature")

	_claim_nonce(site, key_id, nonce)
	return key_id


def _validated_state(state):
	if not isinstance(state, dict):
		raise frappe.ValidationError("state must be a JSON object")
	unknown_keys = set(state) - MANAGED_CONFIG_KEYS
	if unknown_keys:
		raise frappe.ValidationError(
			f"Unsupported enterprise configuration keys: {', '.join(sorted(unknown_keys))}"
		)

	validated = {}
	for key, value in state.items():
		if value is None:
			validated[key] = None
		elif key in INTEGER_CONFIG_KEYS:
			try:
				validated[key] = int(value)
			except (TypeError, ValueError):
				raise frappe.ValidationError(f"{key} must be an integer")
		else:
			if not isinstance(value, (str, int, float, bool)):
				raise frappe.ValidationError(f"{key} must be a scalar value")
			validated[key] = str(value)
	return validated


@frappe.whitelist(allow_guest=True)
def reconcile():
	body, payload = _get_request_body()
	_authenticate_request(body)

	if cint(payload.get("protocol_version")) != PROTOCOL_VERSION:
		raise frappe.ValidationError("Unsupported enterprise management protocol version")
	if payload.get("site") != frappe.local.site:
		raise frappe.AuthenticationError("Management payload site does not match")
	command_id = payload.get("command_id")
	if not isinstance(command_id, str) or not command_id or len(command_id) > 128:
		raise frappe.ValidationError("command_id is required")
	try:
		revision = int(payload.get("revision"))
	except (TypeError, ValueError):
		raise frappe.ValidationError("revision must be an integer")
	if revision <= 0:
		raise frappe.ValidationError("revision must be positive")

	last_revision = cint(frappe.conf.get("enterprise_management_last_revision"))
	if revision <= last_revision:
		return {"status": "already_applied", "revision": last_revision}

	state = _validated_state(payload.get("state"))
	state["enterprise_management_last_revision"] = revision
	_write_site_config(state)
	state_hash = hashlib.sha256(
		json.dumps(payload.get("state"), sort_keys=True, separators=(",", ":")).encode()
	).hexdigest()
	return {"status": "applied", "revision": revision, "state_hash": state_hash}


@frappe.whitelist(allow_guest=True)
def rotate_secret():
	body, payload = _get_request_body()
	_authenticate_request(body)
	new_key_id = payload.get("new_key_id")
	new_secret = payload.get("new_secret")
	_validate_key(new_key_id, new_secret)

	if (
		new_key_id == frappe.conf.get("enterprise_management_key_id")
		and new_secret == frappe.conf.get("enterprise_management_secret")
	):
		return {"status": "already_rotated", "key_id": new_key_id}

	now = int(time.time())
	_write_site_config(
		{
			"enterprise_management_previous_key_id": frappe.conf.get(
				"enterprise_management_key_id"
			),
			"enterprise_management_previous_secret": frappe.conf.get(
				"enterprise_management_secret"
			),
			"enterprise_management_previous_expires_at": now
			+ PREVIOUS_KEY_TTL_SECONDS,
			"enterprise_management_key_id": new_key_id,
			"enterprise_management_secret": new_secret,
		}
	)
	return {"status": "rotated", "key_id": new_key_id}


def enforce_site_enabled():
	if not cint(frappe.conf.get("saas_site_disabled")):
		return
	path = getattr(frappe.request, "path", "") or ""
	if path in MANAGEMENT_METHODS:
		return
	raise frappe.SessionStopped("Site disabled by SaaS administrator")


def generate_secret():
	"""Kept separate for tests and future local provisioning commands."""
	return secrets.token_urlsafe(32)
