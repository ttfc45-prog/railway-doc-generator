"""
main.py
Railway Documentation Generator - Application Entry Point

Run with:
    streamlit run main.py

Bootstraps the application and delegates rendering entirely to ui.render(),
which configures the page, initialises session state, renders the sidebar
and all engineering tabs.
"""

# ── Standard library ──────────────────────────────────────────────────────────
import sys
from pathlib import Path

# Ensure the project root is on sys.path when the script is invoked directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# ── Local imports ──────────────────────────────────────────────────────────────
import ui   # noqa: E402  (import after sys.path fix)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    """
    Top-level entry point.

    All page configuration, state initialisation, sidebar rendering and tab
    rendering is encapsulated in ui.render() to keep this file minimal and
    testable.
    """
    ui.render()


if __name__ == "__main__":
    main()
