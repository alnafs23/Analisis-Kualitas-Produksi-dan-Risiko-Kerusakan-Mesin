
import pandas as pd
from pathlib import Path

# Lokasi dataset
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "ai4i2020.csv"

# Memuat dataset
df = pd.read_csv(DATA_PATH)

print("=" * 60)
print("ANALISIS DATASET AI4I 2020")
print("=" * 60)

# 1. Pemeriksaan awal
print("\n1. INFORMASI DATASET")
print("Ukuran dataset:", df.shape)
print("\nDaftar kolom:")
print(df.columns.tolist())
print("\nTipe data:")
print(df.dtypes)
print("\nNilai kosong:")
print(df.isnull().sum())
print("\nJumlah baris duplikat:", df.duplicated().sum())

# 2. Tingkat kegagalan keseluruhan
failure_col = "Machine failure"

if failure_col not in df.columns:
    raise ValueError(
        f"Kolom '{failure_col}' tidak ditemukan. "
        "Periksa kembali nama kolom dataset."
    )

total_records = len(df)
total_failures = int(df[failure_col].sum())
failure_rate = (
    total_failures / total_records * 100
    if total_records > 0
    else 0
)

print("\n2. RINGKASAN KEGAGALAN")
print("Total catatan:", total_records)
print("Catatan dengan kegagalan:", total_failures)
print(f"Tingkat kegagalan: {failure_rate:.2f}%")

# 3. Tingkat kegagalan berdasarkan tipe mesin
if "Type" in df.columns:
    type_analysis = (
        df.groupby("Type")
        .agg(
            total_records=(failure_col, "size"),
            failure_records=(failure_col, "sum"),
            failure_rate=(failure_col, "mean"),
        )
        .reset_index()
    )

    type_analysis["failure_rate"] *= 100
    type_analysis = type_analysis.sort_values(
        "failure_rate",
        ascending=False,
    )

    print("\n3. KEGAGALAN BERDASARKAN TIPE MESIN")
    print(
        type_analysis.to_string(
            index=False,
            formatters={
                "failure_rate": "{:.2f}%".format
            },
        )
    )

    type_analysis.to_csv(
        BASE_DIR / "analisis_tipe_mesin.csv",
        index=False,
    )

# 4. Distribusi jenis kegagalan
failure_types = [
    "TWF",
    "HDF",
    "PWF",
    "OSF",
    "RNF",
]

available_failure_types = [
    column for column in failure_types
    if column in df.columns
]

if available_failure_types:
    failure_summary = pd.DataFrame({
        "failure_type": available_failure_types,
        "records": [
            int(df[column].sum())
            for column in available_failure_types
        ],
    })

    failure_summary = failure_summary.sort_values(
        "records",
        ascending=False,
    )

    print("\n4. DISTRIBUSI JENIS KEGAGALAN")
    print(failure_summary.to_string(index=False))

    failure_summary.to_csv(
        BASE_DIR / "analisis_jenis_kegagalan.csv",
        index=False,
    )

print("\nAnalisis selesai.")
print("File hasil analisis disimpan di folder proyek.")
