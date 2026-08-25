"""The Daodan universal marketplace compiler.

Markdown and supporting resources under ``plugins/`` are each plugin's content
kernel. TOML sidecars declare component relationships, workflow constraints and
behavioural contracts without embedding prompts. This package loads and
validates those kernels, binds them to a host harness and renders committed
native packages.

Standard library only.
"""
