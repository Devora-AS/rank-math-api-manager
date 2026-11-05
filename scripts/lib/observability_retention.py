"""Observability retention tiers (E6 full) — advisory policy helpers.

RFU-7 auto-TTL cron remains deferred. Operators apply tiers via
`scripts/observability-purge.py --tier` or OBSERVABILITY_RETENTION_TIER.
"""

from __future__ import annotations

from typing import Any

# Named TTL/size tiers for operator-runbook retention (not auto-enforced).
RETENTION_TIERS: dict[str, dict[str, Any]] = {
    "dev": {
        "aliases": ("dev", "short"),
        "max_age_days": 7,
        "max_db_bytes": 52_428_800,  # 50 MiB
        "description": "Short local/dev retention",
    },
    "standard": {
        "aliases": ("standard", "default"),
        "max_age_days": 30,
        "max_db_bytes": 104_857_600,  # 100 MiB
        "description": "Default operator retention",
    },
    "audit": {
        "aliases": ("audit", "long"),
        "max_age_days": 90,
        "max_db_bytes": 524_288_000,  # 500 MiB
        "description": "Longer audit-oriented retention",
    },
}

_ALIAS_TO_CANONICAL: dict[str, str] = {}
for _name, _spec in RETENTION_TIERS.items():
    for _alias in _spec["aliases"]:
        _ALIAS_TO_CANONICAL[str(_alias).lower()] = _name


def resolve_retention_tier(name: str | None) -> dict[str, Any] | None:
    """Return tier policy dict with canonical `name` key, or None if unknown/empty."""
    if name is None:
        return None
    key = str(name).strip().lower()
    if not key:
        return None
    canonical = _ALIAS_TO_CANONICAL.get(key)
    if canonical is None:
        return None
    spec = dict(RETENTION_TIERS[canonical])
    spec["name"] = canonical
    return spec


def list_retention_tiers() -> list[dict[str, Any]]:
    """Return sorted tier summaries for docs/CLI."""
    out: list[dict[str, Any]] = []
    for name in ("dev", "standard", "audit"):
        spec = RETENTION_TIERS[name]
        out.append(
            {
                "name": name,
                "aliases": list(spec["aliases"]),
                "max_age_days": spec["max_age_days"],
                "max_db_bytes": spec["max_db_bytes"],
                "description": spec["description"],
            }
        )
    return out
