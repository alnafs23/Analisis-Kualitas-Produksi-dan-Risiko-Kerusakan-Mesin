
import pandas as pd
import plotly.express as px
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "ai4i2020.csv"


def load_data():
    """Memuat dataset AI4I 2020."""
    return pd.read_csv(DATA_PATH)


def get_failure_summary(df):
    """Menghitung ringkasan kegagalan mesin."""
    total = len(df)
    failures = int(df["Machine failure"].sum())

    return {
        "total_records": total,
        "failure_records": failures,
        "normal_records": total - failures,
        "failure_rate": failures / total * 100 if total else 0,
    }


def get_failure_by_type(df):
    """Menghitung tingkat kegagalan berdasarkan tipe mesin."""
    result = (
        df.groupby("Type")
        .agg(
            total_records=("Machine failure", "size"),
            failure_records=("Machine failure", "sum"),
        )
        .reset_index()
    )

    result["failure_rate"] = (
        result["failure_records"]
        / result["total_records"]
        * 100
    )

    return result.sort_values(
        "failure_rate",
        ascending=False,
    )


def get_failure_type_summary(df):
    """Menghitung jumlah indikator untuk setiap jenis kegagalan."""
    columns = ["TWF", "HDF", "PWF", "OSF", "RNF"]
    available = [column for column in columns if column in df.columns]

    result = pd.DataFrame({
        "Jenis Kegagalan": available,
        "Jumlah Indikator": [
            int(df[column].sum()) for column in available
        ],
    })

    return result.sort_values(
        "Jumlah Indikator",
        ascending=False,
    )


def plot_failure_distribution(df):
    """Grafik catatan normal dan catatan kegagalan."""
    summary = get_failure_summary(df)

    chart_data = pd.DataFrame({
        "Kondisi": ["Normal", "Machine Failure"],
        "Jumlah Catatan": [
            summary["normal_records"],
            summary["failure_records"],
        ],
    })

    return px.bar(
        chart_data,
        x="Kondisi",
        y="Jumlah Catatan",
        title="Distribusi Kondisi Mesin",
        text="Jumlah Catatan",
    )


def plot_failure_by_type(df):
    """Grafik tingkat kegagalan berdasarkan tipe mesin."""
    result = get_failure_by_type(df)

    return px.bar(
        result,
        x="Type",
        y="failure_rate",
        text="failure_rate",
        title="Tingkat Kegagalan Berdasarkan Tipe Mesin",
        labels={
            "Type": "Tipe Mesin",
            "failure_rate": "Tingkat Kegagalan (%)",
        },
    )


def plot_failure_types(df):
    """Grafik jumlah indikator setiap jenis kegagalan."""
    result = get_failure_type_summary(df)

    return px.bar(
        result,
        x="Jenis Kegagalan",
        y="Jumlah Indikator",
        text="Jumlah Indikator",
        title="Distribusi Indikator Jenis Kegagalan",
    )
