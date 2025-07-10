"""
conftest.py – bootstrap for extractor unit-tests
────────────────────────────────────────────────────────────────────────────
• Creates tiny syn_dict.tsv / roles.tsv so tests never depend on real data.
• Replaces heavy WP-7 / WP-9 modules with stubs (registered **before**
  the PipelineRunner import sweep).
• Provides helper wrappers so legacy imports keep working.
• Stubs heavy deps (`dateparser`, `regex`) so CI doesn’t need them.
"""