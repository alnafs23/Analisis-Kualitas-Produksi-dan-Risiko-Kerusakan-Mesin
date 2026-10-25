
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = (
    Path(__file__).resolve().parent
    / "database"
    / "maintenance.db"
)

query = """
    SELECT 'TWF' AS failure_type,
           SUM(twf) AS failure_count
    FROM machine_data

    UNION ALL

    SELECT 'HDF', SUM(hdf)
    FROM machine_data

    UNION ALL

    SELECT 'PWF', SUM(pwf)
    FROM machine_data

    UNION ALL

    SELECT 'OSF', SUM(osf)
    FROM machine_data

    UNION ALL

    SELECT 'RNF', SUM(rnf)
    FROM machine_data

    ORDER BY failure_count DESC;
"""

with sqlite3.connect(DB_PATH) as conn:
    result = pd.read_sql_query(query, conn)

print(result.to_string(index=False))
