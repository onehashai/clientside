import frappe
import time
from dataclasses import dataclass
from urllib.parse import unquote

from werkzeug.wrappers import Response

DEFAULT_WINDOW_SECONDS = 60
DEFAULT_IP_LIMIT = 180
DEFAULT_GLOBAL_LIMIT = 1000

ENDPOINT_DEFAULTS = {
    "dt_message_status_webhook": {
        "ip_limit": 60,
        "global_limit": 180,
        "window": 60,
    },
    "resource:Bin": {
        "ip_limit": 60,
        "global_limit": 240,
        "window": 60,
    }
}


@dataclass
class PlatformRateLimitResponse:
    reset: int
    limit: int

    def update(self):
        pass

    def headers(self):
        return {
            "Retry-After": self.reset,
            "X-RateLimit-Limit": self.limit,
            "X-RateLimit-Remaining": 0,
            "X-RateLimit-Reset": self.reset,
        }

    def respond(self):
        return Response("Too Many Requests", status=429)


def enforce_api_rate_limit():
    if not frappe.request:
        return

    endpoint = get_api_endpoint_from_path(frappe.request.path)
    if not endpoint:
        return

    config = get_rate_limit_config(endpoint)
    if not config.get("enabled", True):
        return

    window = int(config.get("window") or DEFAULT_WINDOW_SECONDS)
    ip_limit = int(config.get("ip_limit") or DEFAULT_IP_LIMIT)
    global_limit = int(config.get("global_limit") or DEFAULT_GLOBAL_LIMIT)
    site = frappe.local.site or "unknown-site"
    ip = frappe.local.request_ip or "unknown-ip"

    checks = (
        (f"platform-api-rl:{site}:{endpoint}:global", global_limit),
        (f"platform-api-rl:{site}:{endpoint}:ip:{ip}", ip_limit),
    )

    for key, limit in checks:
        count, reset = increment_window(key, window)
        if count > limit:
            frappe.local.rate_limiter = PlatformRateLimitResponse(reset=reset, limit=limit)
            raise frappe.TooManyRequestsError


def get_api_endpoint_from_path(path):
    method_prefixes = ("/api/method/", "/api/v1/method/", "/api/v2/method/")
    for prefix in method_prefixes:
        if path.startswith(prefix):
            return unquote(path[len(prefix) :].split("/", 1)[0])

    resource_prefixes = ("/api/resource/", "/api/v1/resource/", "/api/v2/document/")
    for prefix in resource_prefixes:
        if path.startswith(prefix):
            return "resource:" + unquote(path[len(prefix) :].split("/", 1)[0])

    doctype_prefixes = ("/api/v2/doctype/",)
    for prefix in doctype_prefixes:
        if path.startswith(prefix):
            return "doctype:" + unquote(path[len(prefix) :].split("/", 1)[0])

    return None


def get_rate_limit_config(endpoint):
    config = frappe.conf.get("platform_api_rate_limit") or {}
    default_config = {
        "enabled": config.get("enabled", True),
        "window": config.get("window", DEFAULT_WINDOW_SECONDS),
        "ip_limit": config.get("ip_limit", DEFAULT_IP_LIMIT),
        "global_limit": config.get("global_limit", DEFAULT_GLOBAL_LIMIT),
    }

    endpoint_config = ENDPOINT_DEFAULTS.get(endpoint, {}).copy()
    endpoint_config.update((config.get("endpoints") or {}).get(endpoint, {}))

    default_config.update(endpoint_config)
    return default_config


def increment_window(key, window):
    timestamp = int(time.time())
    window_number, spent = divmod(timestamp, window)
    cache_key = frappe.cache.make_key(f"{key}:{window_number}")
    reset = window - spent

    pipeline = frappe.cache.pipeline()
    pipeline.incr(cache_key)
    pipeline.expire(cache_key, window + 5)
    result = pipeline.execute()

    return int(result[0]), reset
