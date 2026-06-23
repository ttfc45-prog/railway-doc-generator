"""
excel_import.py
Railway Documentation Generator - Data Import Module
Handles import of project parameters from Excel, CSV, and other file formats.
"""

import io
import pandas as pd
from pathlib import Path
from project_database import ProjectDatabase as PDB


class DataImporter:
    """Utilities for importing railway project data from external files."""

    # ─────────────────────────────────────────
    # Excel Import
    # ─────────────────────────────────────────

    @staticmethod
    def import_from_excel(file_obj) -> dict:
        """
        Read project parameters from an Excel file.
        Expects a sheet named 'Parameters' with two columns: Parameter | Value.
        Returns a dict suitable for PDB.update().
        """
        try:
            xls  = pd.ExcelFile(file_obj)
            data = {}

            # Try to read 'Parameters' sheet
            if "Parameters" in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name="Parameters", header=0)
                df.columns = [str(c).strip() for c in df.columns]
                key_col = df.columns[0]
                val_col = df.columns[1] if len(df.columns) > 1 else None
                if val_col:
                    for _, row in df.iterrows():
                        k = str(row[key_col]).strip()
                        v = row[val_col]
                        if k and k != "nan":
                            data[k] = v

            # Try to read station list
            if "Stations" in xls.sheet_names:
                df_st = pd.read_excel(xls, sheet_name="Stations")
                stations = df_st.iloc[:, 0].dropna().astype(str).tolist()
                if stations:
                    data["station_list"] = stations
                    data["number_of_stations"] = len(stations)

            # Try to read rolling stock sheet
            if "Rolling Stock" in xls.sheet_names:
                df_rs = pd.read_excel(xls, sheet_name="Rolling Stock", header=0)
                df_rs.columns = [str(c).strip() for c in df_rs.columns]
                if len(df_rs.columns) >= 2:
                    for _, row in df_rs.iterrows():
                        k = str(row.iloc[0]).strip()
                        v = row.iloc[1]
                        if k and k != "nan":
                            data[k] = v

            return data
        except Exception as e:
            return {"_import_error": str(e)}

    # ─────────────────────────────────────────
    # CSV Import
    # ─────────────────────────────────────────

    @staticmethod
    def import_from_csv(file_obj) -> dict:
        """
        Read project parameters from a CSV file.
        Expects columns: parameter, value
        """
        try:
            df = pd.read_csv(file_obj, header=0)
            df.columns = [str(c).strip().lower() for c in df.columns]
            if "parameter" in df.columns and "value" in df.columns:
                return {
                    str(row["parameter"]).strip(): row["value"]
                    for _, row in df.iterrows()
                    if str(row["parameter"]).strip() not in ("nan", "")
                }
            elif len(df.columns) >= 2:
                return {
                    str(row.iloc[0]).strip(): row.iloc[1]
                    for _, row in df.iterrows()
                    if str(row.iloc[0]).strip() not in ("nan", "")
                }
            return {}
        except Exception as e:
            return {"_import_error": str(e)}

    # ─────────────────────────────────────────
    # Station list import
    # ─────────────────────────────────────────

    @staticmethod
    def import_station_list(file_obj, format: str = "excel") -> list[str]:
        """
        Import a list of station names from a single-column Excel or CSV file.
        """
        try:
            if format == "csv":
                df = pd.read_csv(file_obj, header=None)
            else:
                df = pd.read_excel(file_obj, header=None)
            stations = df.iloc[:, 0].dropna().astype(str).tolist()
            return [s.strip() for s in stations if s.strip() and s.strip() != "nan"]
        except Exception:
            return []

    # ─────────────────────────────────────────
    # Type coercion helpers
    # ─────────────────────────────────────────

    @staticmethod
    def _coerce_value(val):
        """Try to convert imported string values to appropriate Python types."""
        if isinstance(val, (int, float, bool, list)):
            return val
        s = str(val).strip()
        # Boolean
        if s.lower() in ("true", "yes", "1"):
            return True
        if s.lower() in ("false", "no", "0"):
            return False
        # Integer
        try:
            return int(s)
        except ValueError:
            pass
        # Float
        try:
            return float(s)
        except ValueError:
            pass
        return s

    @classmethod
    def apply_to_db(cls, imported: dict) -> tuple[int, list[str]]:
        """
        Apply imported data to ProjectDatabase.
        Returns (count_applied, list_of_warnings).
        """
        warnings = []
        applied  = 0
        for k, v in imported.items():
            if k.startswith("_"):
                warnings.append(f"Skipped internal key: {k} = {v}")
                continue
            coerced = cls._coerce_value(v)
            PDB.set(k, coerced)
            applied += 1
        return applied, warnings

    # ─────────────────────────────────────────
    # Export template generator
    # ─────────────────────────────────────────

    @staticmethod
    def generate_import_template() -> bytes:
        """
        Generate a downloadable Excel template showing all importable parameters.
        """
        from config import DEFAULT_PROJECT
        rows = [(k, v) for k, v in DEFAULT_PROJECT.items() if not isinstance(v, list)]
        df   = pd.DataFrame(rows, columns=["Parameter", "Value"])

        buf  = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Parameters", index=False)
            # Station sheet
            stations_df = pd.DataFrame(
                {"Station Name": [f"Station {i+1:02d}" for i in range(18)]}
            )
            stations_df.to_excel(writer, sheet_name="Stations", index=False)

        buf.seek(0)
        return buf.read()
