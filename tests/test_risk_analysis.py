
import pandas as pd

from analytics.risk_analysis import (
    get_failure_summary,
    get_failure_by_type,
    get_failure_type_summary,
)


def test_failure_summary():
    df = pd.DataFrame({
        "Machine failure": [0, 1, 0, 1],
    })

    result = get_failure_summary(df)

    assert result["total_records"] == 4
    assert result["failure_records"] == 2
    assert result["normal_records"] == 2
    assert result["failure_rate"] == 50.0


def test_failure_by_type():
    df = pd.DataFrame({
        "Type": ["L", "L", "M", "M"],
        "Machine failure": [0, 1, 0, 0],
    })

    result = get_failure_by_type(df)

    low = result[result["Type"] == "L"].iloc[0]
    medium = result[result["Type"] == "M"].iloc[0]

    assert low["failure_records"] == 1
    assert low["failure_rate"] == 50.0
    assert medium["failure_rate"] == 0.0


def test_failure_type_summary():
    df = pd.DataFrame({
        "TWF": [1, 0, 1],
        "HDF": [0, 1, 0],
        "PWF": [0, 0, 0],
        "OSF": [0, 0, 1],
        "RNF": [0, 0, 0],
    })

    result = get_failure_type_summary(df)

    counts = dict(zip(
        result["Jenis Kegagalan"],
        result["Jumlah Indikator"],
    ))

    assert counts["TWF"] == 2
    assert counts["HDF"] == 1
    assert counts["PWF"] == 0
    assert counts["OSF"] == 1
    assert counts["RNF"] == 0

