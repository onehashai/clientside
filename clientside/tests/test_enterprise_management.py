import hashlib
import hmac
import json
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import frappe

from clientside import enterprise_management


class FakeNonceCache:
	def __init__(self):
		self.keys = set()

	def make_key(self, key, shared=False):
		return key

	def set(self, key, value, nx=False, ex=None):
		if nx and key in self.keys:
			return False
		self.keys.add(key)
		return True


class TestEnterpriseManagement(TestCase):
	def signed_request(self, body, secret="a" * 32, nonce="nonce-1"):
		timestamp = 2_000_000_000
		path = "/api/method/clientside.enterprise_management.reconcile"
		canonical = "\n".join(
			("POST", path, str(timestamp), nonce, hashlib.sha256(body).hexdigest())
		).encode()
		signature = hmac.new(secret.encode(), canonical, hashlib.sha256).hexdigest()
		return SimpleNamespace(
			method="POST",
			path=path,
			headers={
				"X-Bettersaas-Key-Id": "emk_test_key",
				"X-Bettersaas-Nonce": nonce,
				"X-Bettersaas-Site": "enterprise.test",
				"X-Bettersaas-Signature": f"sha256={signature}",
				"X-Bettersaas-Timestamp": str(timestamp),
			},
		)

	def test_signed_request_is_accepted_once(self):
		body = json.dumps({"state": {}}).encode()
		request = self.signed_request(body)
		cache = FakeNonceCache()
		with (
			patch.object(enterprise_management.time, "time", return_value=2_000_000_000),
			patch.object(enterprise_management.frappe, "request", request),
			patch.object(
				enterprise_management.frappe,
				"local",
				SimpleNamespace(site="enterprise.test"),
			),
			patch.object(
				enterprise_management.frappe,
				"conf",
				{
					"enterprise_management_key_id": "emk_test_key",
					"enterprise_management_secret": "a" * 32,
				},
			),
			patch.object(enterprise_management.frappe, "cache", return_value=cache),
		):
			self.assertEqual(
				enterprise_management._authenticate_request(body), "emk_test_key"
			)
			with self.assertRaises(frappe.AuthenticationError):
				enterprise_management._authenticate_request(body)

	def test_tampered_body_is_rejected(self):
		body = b'{"state":{}}'
		request = self.signed_request(body)
		with (
			patch.object(enterprise_management.time, "time", return_value=2_000_000_000),
			patch.object(enterprise_management.frappe, "request", request),
			patch.object(
				enterprise_management.frappe,
				"local",
				SimpleNamespace(site="enterprise.test"),
			),
			patch.object(
				enterprise_management.frappe,
				"conf",
				{
					"enterprise_management_key_id": "emk_test_key",
					"enterprise_management_secret": "a" * 32,
				},
			),
			patch.object(
				enterprise_management.frappe,
				"cache",
				return_value=FakeNonceCache(),
			),
		):
			with self.assertRaises(frappe.AuthenticationError):
				enterprise_management._authenticate_request(body + b" ")

	def test_state_allowlist_and_integer_normalisation(self):
		self.assertEqual(
			enterprise_management._validated_state(
				{"min_license": "25", "subscription_status": "active"}
			),
			{"min_license": 25, "subscription_status": "active"},
		)
		with self.assertRaises(frappe.ValidationError):
			enterprise_management._validated_state({"db_password": "not-allowed"})

	def test_disabled_site_keeps_only_management_endpoint_open(self):
		with (
			patch.object(
				enterprise_management.frappe, "conf", {"saas_site_disabled": 1}
			),
			patch.object(
				enterprise_management.frappe,
				"request",
				SimpleNamespace(path="/api/method/frappe.auth.get_logged_user"),
			),
		):
			with self.assertRaises(frappe.SessionStopped):
				enterprise_management.enforce_site_enabled()

		with (
			patch.object(
				enterprise_management.frappe, "conf", {"saas_site_disabled": 1}
			),
			patch.object(
				enterprise_management.frappe,
				"request",
				SimpleNamespace(
					path="/api/method/clientside.enterprise_management.reconcile"
				),
			),
		):
			self.assertIsNone(enterprise_management.enforce_site_enabled())
