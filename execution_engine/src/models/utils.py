import pandas as pd
import os

class SecurityException(Exception):
    """Raised when an operation attempts to breach path security guards."""
    pass

def resolve_secure_path(requested_path: str) -> str:
    """
    Safely resolves the absolute path of the requested dataset.
    Verifies that the target path is strictly within the allowed data directories 
    ('data' or 'uploads') to prevent Path Traversal (LFI) attacks.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    # Strip leading slashes to prevent absolute path override trick
    clean_path = requested_path.lstrip("/\\")
    
    final_path = os.path.abspath(os.path.join(project_root, clean_path))
    
    # Allowed directories
    allowed_zones = [
        os.path.join(project_root, "data"),
        os.path.join(project_root, "uploads")
    ]
    
    # Ensure final_path starts with one of the allowed zones
    is_safe = any(final_path.startswith(zone) for zone in allowed_zones)
    
    if not is_safe:
        raise SecurityException(
            f"Path Traversal Blocked: Requested dataset '{requested_path}' resolves outside allowed safe zones."
        )
        
    return final_path


def load_csv(path: str, date_col: str) -> pd.DataFrame:
    """
    Load the Superstore CSV with correct encoding and date parsing.
    Superstore uses latin1 encoding and DD-MM-YYYY date format.
    """
    df = pd.read_csv(path, encoding='latin1')
    df[date_col] = pd.to_datetime(df[date_col], dayfirst=True)
    return df


def apply_filters(df: pd.DataFrame, filters: list) -> pd.DataFrame:
    """Apply a list of filter dicts to a DataFrame."""
    for f in filters:
        col = f.get("column")
        op = f.get("operator", "equals")
        val = f.get("value")

        if col not in df.columns:
            continue

        if op == "equals":
            df = df[df[col] == val]
        elif op == "not_equals":
            df = df[df[col] != val]
        elif op == "ge":
            df = df[df[col] >= val]
        elif op == "le":
            df = df[df[col] <= val]
        elif op == "contains":
            df = df[df[col].astype(str).str.contains(str(val), case=False)]

    return df