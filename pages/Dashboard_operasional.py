
import streamlit as st
import pandas as pd

from database.connection import get_connection

st.set_page_config(
    page_title="Dashboard Operasional | MIMS",
    layout="wide",
)

st.title("Dashboard Operasional MIMS")
st.write(
    "Ringkasan aset, kerusakan, pekerjaan perbaikan, "
    "dan jadwal pemeliharaan mesin."
)

conn = get_connection()

try:
    # Ringkasan aset
    total_assets = conn.execute(
        "SELECT COUNT(*) FROM assets"
    ).fetchone()[0]

    # Laporan kerusakan yang belum selesai
    open_reports = conn.execute(
        """
        SELECT COUNT(*)
        FROM failure_reports
        WHERE status != 'Selesai'
        """
    ).fetchone()[0]

    # Work Order yang belum selesai atau dibatalkan
    active_orders = conn.execute(
        """
        SELECT COUNT(*)
        FROM work_orders
        WHERE status NOT IN ('Selesai', 'Dibatalkan')
        """
    ).fetchone()[0]

    # Jadwal aktif yang sudah melewati tanggal perawatan
    overdue_schedules = conn.execute(
        """
        SELECT COUNT(*)
        FROM maintenance_schedules
        WHERE status = 'Aktif'
          AND next_maintenance_date < date('now', 'localtime')
        """
    ).fetchone()[0]

    # Data status Work Order
    order_status = pd.read_sql_query(
        """
        SELECT status AS Status, COUNT(*) AS Jumlah
        FROM work_orders
        GROUP BY status
        ORDER BY Jumlah DESC
        """,
        conn,
    )

    # Data laporan berdasarkan prioritas
    report_priority = pd.read_sql_query(
        """
        SELECT priority AS Prioritas, COUNT(*) AS Jumlah
        FROM failure_reports
        WHERE status != 'Selesai'
        GROUP BY priority
        ORDER BY Jumlah DESC
        """,
        conn,
    )

    # Jadwal perawatan terdekat
    upcoming = pd.read_sql_query(
        """
        SELECT
            a.asset_code AS 'Kode Aset',
            a.asset_name AS 'Nama Mesin',
            ms.schedule_name AS 'Jenis Perawatan',
            ms.next_maintenance_date AS 'Tanggal Berikutnya',
            ms.assigned_to AS 'Penanggung Jawab'
        FROM maintenance_schedules ms
        JOIN assets a ON a.id = ms.asset_id
        WHERE ms.status = 'Aktif'
        ORDER BY ms.next_maintenance_date ASC
        LIMIT 10
        """,
        conn,
    )

    # Riwayat log perawatan
    recent_logs = pd.read_sql_query(
        """
        SELECT
            a.asset_code AS 'Kode Aset',
            w.title AS Pekerjaan,
            ml.action_taken AS Tindakan,
            ml.duration_minutes AS 'Durasi (Menit)',
            ml.performed_by AS Teknisi,
            ml.created_at AS 'Waktu Pencatatan'
        FROM maintenance_logs ml
        JOIN work_orders w ON w.id = ml.work_order_id
        JOIN assets a ON a.id = w.asset_id
        ORDER BY ml.id DESC
        LIMIT 10
        """,
        conn,
    )

finally:
    conn.close()

# KPI
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Aset", total_assets)
c2.metric("Laporan Belum Selesai", open_reports)
c3.metric("Work Order Aktif", active_orders)
c4.metric("Jadwal Terlambat", overdue_schedules)

st.divider()

# Visualisasi
left, right = st.columns(2)

with left:
    st.subheader("Status Work Order")

    if order_status.empty:
        st.info("Belum ada Work Order.")
    else:
        st.bar_chart(
            order_status.set_index("Status")["Jumlah"]
        )

with right:
    st.subheader("Prioritas Laporan Kerusakan")

    if report_priority.empty:
        st.info("Belum ada laporan yang belum selesai.")
    else:
        st.bar_chart(
            report_priority.set_index("Prioritas")["Jumlah"]
        )

st.divider()

st.subheader("Jadwal Perawatan Aktif")

if upcoming.empty:
    st.info("Belum ada jadwal perawatan aktif.")
else:
    st.dataframe(
        upcoming,
        use_container_width=True,
        hide_index=True,
    )

st.divider()

st.subheader("Riwayat Perawatan Terbaru")

if recent_logs.empty:
    st.info("Belum ada log perawatan.")
else:
    st.dataframe(
        recent_logs,
        use_container_width=True,
        hide_index=True,
    )

st.caption(
    "Dashboard ini menggunakan data operasional MIMS. "
    "Angka akan berubah mengikuti data yang dimasukkan."
)
