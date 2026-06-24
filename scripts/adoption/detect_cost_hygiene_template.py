"""Deterministic .cursorignore template key selection for MAT cost hygiene (bootstrap + tests)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Keys must match adoption layout `cursorignore_template_keys` / validator template list
TEMPLATE_WORDPRESS = "wordpress"
TEMPLATE_RAILS = "rails"
TEMPLATE_NODE = "node"
TEMPLATE_PYTHON = "python"
TEMPLATE_DEFAULT = "default"

ALL_STACK_KEYS: tuple[str, ...] = (
    TEMPLATE_DEFAULT,
    TEMPLATE_NODE,
    TEMPLATE_PYTHON,
    TEMPLATE_RAILS,
    TEMPLATE_WORDPRESS,
)


@dataclass
class TemplateDetection:
    key: str
    reason: str
    signals: dict[str, bool] = field(default_factory=dict)
    as_dict: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.as_dict = {
            "key": self.key,
            "reason": self.reason,
            "signals": dict(self.signals),
        }


def detect_cursorignore_template_key(root: Path) -> TemplateDetection:
    """Select template key. Priority: WordPress → Rails (explicit app) → Node (package.json) → Python.

    Ambiguous repos fall back to the generic default. ``Gemfile`` without Node markers selects
    the Rails-oriented template (tmp/log/storage) as a reasonable ignore surface for Ruby worktrees.
    """
    root = root.resolve()
    sig = {
        "wp_config": (root / "wp-config.php").is_file(),
        "rails_app_rb": (root / "config" / "application.rb").is_file(),
        "package_json": (root / "package.json").is_file(),
        "gemfile": (root / "Gemfile").is_file(),
    }
    if sig["wp_config"]:
        return TemplateDetection(
            TEMPLATE_WORDPRESS, "Found wp-config.php (WordPress).", {"wp_config": True}
        )
    if sig["rails_app_rb"]:
        return TemplateDetection(
            TEMPLATE_RAILS, "Found config/application.rb (Rails).", {"rails_app_rb": True}
        )
    if sig["package_json"]:
        return TemplateDetection(
            TEMPLATE_NODE, "Found package.json (Node / JS toolchain).", {"package_json": True}
        )
    for path in ("pyproject.toml", "requirements.txt", "Pipfile", "setup.py"):
        p = root / path
        if p.is_file():
            return TemplateDetection(
                TEMPLATE_PYTHON, f"Found {path} (Python).", {f"has_{path}": True}
            )
    if sig["gemfile"]:
        return TemplateDetection(
            TEMPLATE_RAILS, "Found Gemfile without package.json (Ruby / likely Rails or Rack).", {"gemfile": True}
        )
    return TemplateDetection(
        TEMPLATE_DEFAULT, "No strong stack markers; using generic MAT default template.", {}
    )
