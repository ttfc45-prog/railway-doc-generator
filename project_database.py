"""
project_database.py
Railway Documentation Generator — ProjectDatabase
==================================================

Persistence layer for ProjectModel inputs ONLY.

STRICT RULE: This module stores and retrieves primitive user inputs.
It never stores, caches, or retrieves calculated outputs.
Any attempt to store a forbidden key is rejected with a ValueError.

Architecture:
    UI → ProjectDatabase (session_state) → ProjectModel → CalculationEngine
    CalculatedState flows FORWARD only — never written back here.
"""

import json
import copy
from pathlib import Path

# Lazy import: streamlit may not be available in test environments
try:
    import streamlit as st
except ImportError:
    class _FakeSt:
        class session_state(dict): pass
    st = _FakeSt()
    st.session_state = {}

from project_model import ProjectModel, DEFAULT_INPUTS
from config import DATA_DIR


class ProjectDatabase:
    """
    Thin session-state wrapper around ProjectModel inputs.

    All engineering numbers (commercial speed, fleet size, etc.) are
    EXCLUDED from storage. They are always derived fresh from CalculationEngine.
    """

    SESSION_KEY = "rdg_project_inputs_v2"   # versioned to avoid stale state

    # ── Initialisation ────────────────────────────────────────────────────────

    @classmethod
    def initialise(cls) -> None:
        """Seed session_state with default inputs if not already present."""
        if cls.SESSION_KEY not in st.session_state:
            st.session_state[cls.SESSION_KEY] = copy.deepcopy(DEFAULT_INPUTS)

    # ── Model access ──────────────────────────────────────────────────────────

    @classmethod
    def get_model(cls) -> ProjectModel:
        """Return a fresh ProjectModel built from the stored inputs."""
        cls.initialise()
        return ProjectModel(st.session_state[cls.SESSION_KEY])

    @classmethod
    def get_all(cls) -> dict:
        """Return a copy of stored inputs as a plain dict."""
        cls.initialise()
        return copy.deepcopy(st.session_state[cls.SESSION_KEY])

    # ── Getters / Setters (with forbidden-key enforcement) ────────────────────

    @classmethod
    def get(cls, key: str, default=None):
        cls.initialise()
        return st.session_state[cls.SESSION_KEY].get(key, default)

    @classmethod
    def set(cls, key: str, value) -> None:
        """Set a single input value. Raises ValueError for calculated outputs."""
        cls.initialise()
        if key in ProjectModel._FORBIDDEN_KEYS:
            raise ValueError(
                f"ProjectDatabase.set('{key}') rejected — '{key}' is a calculated "
                f"output. Read it from CalculatedState, not from the database."
            )
        st.session_state[cls.SESSION_KEY][key] = value

    @classmethod
    def update(cls, data: dict) -> None:
        """Batch update. Raises ValueError if any forbidden key is present."""
        cls.initialise()
        forbidden = [k for k in data if k in ProjectModel._FORBIDDEN_KEYS]
        if forbidden:
            raise ValueError(
                f"ProjectDatabase.update() rejected forbidden key(s): {forbidden}. "
                f"These are calculated outputs and must never be stored."
            )
        st.session_state[cls.SESSION_KEY].update(data)

    # ── Persistence ───────────────────────────────────────────────────────────

    @classmethod
    def save_to_file(cls, filepath: Path | None = None) -> Path:
        """Serialise the project inputs to JSON."""
        cls.initialise()
        if filepath is None:
            safe_name = cls.get("project_name", "project").replace(" ", "_")
            filepath = DATA_DIR / f"{safe_name}.json"
        model = cls.get_model()
        model.save_to_file(filepath)
        return filepath

    @classmethod
    def load_from_file(cls, filepath: Path) -> None:
        """Load project inputs from a JSON file."""
        model = ProjectModel.from_file(filepath)
        st.session_state[cls.SESSION_KEY] = model.to_dict()

    @classmethod
    def reset_to_defaults(cls) -> None:
        """Restore all parameters to factory defaults."""
        st.session_state[cls.SESSION_KEY] = copy.deepcopy(DEFAULT_INPUTS)

    # ── Convenience (inputs only) ─────────────────────────────────────────────

    @classmethod
    def get_station_list(cls) -> list[str]:
        model = cls.get_model()
        return model.get_station_list()

    @classmethod
    def as_summary_dict(cls) -> dict:
        """Return a condensed header dict — no calculated values."""
        model = cls.get_model()
        return model.summary()
