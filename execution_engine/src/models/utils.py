import pandas as pd


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