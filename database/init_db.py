
from database.connection import get_connection


def init_db():
    conn = get_connection()

    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_code TEXT NOT NULL UNIQUE,
            asset_name TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT,
            manufacturer TEXT,
            status TEXT NOT NULL DEFAULT 'active'
                CHECK (status IN ('active', 'inactive', 'maintenance')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS failure_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            reported_by TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'medium'
                CHECK (priority IN ('low', 'medium', 'high', 'critical')),
            status TEXT NOT NULL DEFAULT 'open'
                CHECK (status IN ('open', 'investigating', 'resolved', 'cancelled')),
            reported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            resolved_at TEXT,
            FOREIGN KEY (asset_id) REFERENCES assets(id)
        );

        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_order_code TEXT NOT NULL UNIQUE,
            asset_id INTEGER NOT NULL,
            failure_report_id INTEGER,
            assigned_to TEXT,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT NOT NULL DEFAULT 'medium',
            status TEXT NOT NULL DEFAULT 'open'
                CHECK (status IN ('open', 'in_progress', 'completed', 'cancelled')),
            planned_date TEXT,
            started_at TEXT,
            completed_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (asset_id) REFERENCES assets(id),
            FOREIGN KEY (failure_report_id) REFERENCES failure_reports(id)
        );

        CREATE TABLE IF NOT EXISTS maintenance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_order_id INTEGER NOT NULL,
            action_taken TEXT NOT NULL,
            findings TEXT,
            duration_minutes INTEGER,
            performed_by TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (work_order_id) REFERENCES work_orders(id)
        );

        CREATE TABLE IF NOT EXISTS maintenance_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            schedule_name TEXT NOT NULL,
            maintenance_type TEXT NOT NULL,
            interval_days INTEGER NOT NULL CHECK (interval_days > 0),
            last_maintenance_date TEXT,
            next_maintenance_date TEXT NOT NULL,
            assigned_to TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            FOREIGN KEY (asset_id) REFERENCES assets(id)
        );
        """)

        conn.commit()
        print("Tabel operasional MIMS berhasil dibuat.")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
