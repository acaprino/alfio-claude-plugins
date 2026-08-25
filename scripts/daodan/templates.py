"""Template substitution with an allowlisted context.

Rendering uses ``string.Template`` rather than a general templating language on
purpose: a generated marketplace should not be able to run logic, and every
substitution name a template may use is enumerated here. An unknown placeholder
is an error, never an empty string.
"""

from __future__ import annotations

from pathlib import Path
from string import Template
from typing import Mapping

#: Every name a layout path or a manifest template may substitute.
ALLOWED_KEYS: frozenset[str] = frozenset(
    {
        "plugin",
        "version",
        "description",
        "license",
        "host",
        "skill",
        "role",
        "workflow",
        "marketplace",
        "adapter_version",
        "author",
        "body",
        "name",
        "description",
        "tools",
        "agents",
        "roles",
        "strategy",
        "role_delivery",
        "isolation",
        "join",
    }
)


class TemplateError(ValueError):
    pass


def render_template(template: str, context: Mapping[str, str]) -> str:
    """Substitute ``context`` into ``template``, rejecting anything unexpected."""
    unknown = sorted(set(context) - ALLOWED_KEYS)
    if unknown:
        raise TemplateError(f"context key(s) outside the allowlist: {', '.join(unknown)}")
    try:
        return Template(template).substitute(context)
    except KeyError as error:
        raise TemplateError(f"template references unknown placeholder {error.args[0]!r}") from error
    except ValueError as error:
        raise TemplateError(f"malformed template: {error}") from error


def render_path(template: str, context: Mapping[str, str]) -> Path:
    """Substitute into a layout path and return it as a relative path."""
    rendered = render_template(template, context)
    candidate = Path(rendered.replace("\\", "/"))
    if candidate.is_absolute() or ".." in candidate.parts:
        raise TemplateError(f"layout path escapes its package: {rendered}")
    return candidate
