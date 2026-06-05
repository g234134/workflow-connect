"""Optional extension hooks for Gov Core pipelines (Sprint 1 · B-1)."""

from hooks.context_entry_hooks import (
    apply_post_context_entry_hooks,
    apply_pre_context_entry_hooks,
    context_entry_hooks_enabled,
    post_context_entry_hook,
    pre_context_entry_hook,
)

__all__ = [
    "apply_post_context_entry_hooks",
    "apply_pre_context_entry_hooks",
    "context_entry_hooks_enabled",
    "post_context_entry_hook",
    "pre_context_entry_hook",
]
