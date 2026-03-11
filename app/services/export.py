import pandas as pd


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convertit un DataFrame en CSV UTF-8 telechargeable."""
    if df is None or df.empty:
        return b""

    export_df = df.copy()
    for column in export_df.select_dtypes(include=["datetime", "datetimetz"]).columns:
        export_df[column] = pd.to_datetime(export_df[column]).dt.strftime("%Y-%m-%d")

    return export_df.to_csv(index=False).encode("utf-8")
