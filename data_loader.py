
import sqlite3
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "ai4i2020.csv"
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "maintenance.db"

DB_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(CSV_PATH)

df = df.rename(columns={
    "UDI": "udi",
    "Product ID": "product_id",
    "Type": "machine_type",
    "Air temperature [K]": "air_temperature_k",
    "Process temperature [K]": "process_temperature_k",
    "Rotational speed [rpm]": "rotational_speed_rpm",
    "Torque [Nm]": "torque_nm",
    "Tool wear [min]": "tool_wear_min",
    "Machine failure": "machine_failure",
    "TWF": "twf",
    "HDF": "hdf",
    "PWF": "pwf",
    "OSF": "osf",
    "RNF": "rnf"
})

with sqlite3.connect(DB_PATH) as conn:
    df.to_sql(
        "machine_data",
        conn,
        if_exists="replace",
        index=False
    )

    result = pd.read_sql_query(
        "SELECT COUNT(*) AS total_records FROM machine_data",
        conn
    )

    print("Database berhasil dibuat!")
    print("Lokasi database:", DB_PATH)
    print("Jumlah data:", result.iloc[0]["total_records"])
