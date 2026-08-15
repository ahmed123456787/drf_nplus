"""
Reads configuration from Django settings under the `DRF_NPLUS` dict.

Example (settings.py):

    DRF_NPLUS = {
        "ENABLED": DEBUG,
        "LOGGER": "drf_nplus",
        "LOG_LEVEL": "WARNING",
        "THRESHOLD": 2,
        "IGNORE_PATHS": ["/admin/", "/static/"],
        "RESPONSE_HEADERS": True,
    }
"""

from django.conf import settings

DEFAULTS = {
    "ENABLED": True,
    "LOGGER": "drf_nplus",
    "LOG_LEVEL": "WARNING",
    "THRESHOLD": 2,
    "IGNORE_PATHS": (),
    "RESPONSE_HEADERS": True,
}


def get(key: str):
    user = getattr(settings, "DRF_NPLUS", {}) or {}
    return user.get(key, DEFAULTS[key])
