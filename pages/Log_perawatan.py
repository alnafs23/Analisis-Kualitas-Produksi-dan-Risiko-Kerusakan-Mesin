
import streamlit as st
import pandas as pd

from database.connection import get_connection

st.set_page_config(
    page_title="Log Perawatan | MIMS",
    layout="wide",
)

st.title("Log Perawatan Mesin")
st.write("Catat tindakan dan hasil pekerjaan perawatan mesin.")

conn = get_connection()

try:
    orders = pd.read_sql_query(
        """
        SELECT
            id,
            work_order_code,
            title,
            asset_id,
            status
        FROM work_orders
        WHERE status = 'Selesai'
        ORDER BY id DESC
        """,
        conn,
    )

    logs = pd.read_sql_query(
        """
        SELECT
            ml.id,
            w.work_order_code AS 'Kode Work Order',
            a.asset_code AS 'Kode Aset',
            a.asset_name AS 'Nama Mesin',
            w.title AS 'Pekerjaan',
            ml.action_taken AS 'Tindakan',
            ml.findings AS 'Temuan',
            ml.duration_minutes AS 'Durasi (Menit)',
            ml.performed_by AS Teknisi,
            ml.created_at AS 'Waktu Pencatatan'
        FROM maintenance_logs ml
        JOIN work_orders w ON w.id = ml.work_order_id
        JOIN assets a ON a.id = w.asset_id
        ORDER BY ml.id DESC
        """,
        conn,
    )
finally:
    conn.close()

st.subheader("Tambah Log Perawatan")

if orders.empty:
    st.info(
        "Belum ada Work Order berstatus Selesai. "
        "Selesaikan satu Work Order terlebih dahulu."
    )
else:
    with st.form("form_log_perawatan"):
        order_options = {
            f"{row.work_order_code} — {row.title}": row.id
            for row in orders.itertuples(index=False)
        }

        selected_order = st.selectbox(
            "Work Order yang diselesaikan",
            list(order_options.keys()),
        )

        action_taken = st.text_area(
            "Tindakan yang dilakukan",
            placeholder="Contoh: Pemeriksaan dan pelumasan komponen.",
        )

        findings = st.text_area(
            "Temuan setelah perawatan",
            placeholder="Contoh: Komponen berfungsi normal setelah pemeriksaan.",
        )

        duration_minutes = st.number_input(
            "Durasi pekerjaan (menit)",
            min_value=1,
            max_value=100000,
            value=30,
            step=5,
        )

        performed_by = st.text_input(
            "Nama teknisi",
            placeholder="Nama teknisi yang melakukan pekerjaan",
        )

        submitted = st.form_submit_button(
            "Simpan Log",
            use_container_width=True,
        )

        if submitted:
            if not action_taken.strip() or not performed_by.strip():
                st.error(
                    "Tindakan dan nama teknisi wajib diisi."
                )
            else:
                conn = get_connection()

                try:
                    conn.execute(
                        """
                        INSERT INTO maintenance_logs (
                            work_order_id,
                            action_taken,
                            findings,
                            duration_minutes,
                            performed_by
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            order_options[selected_order],
                            action_taken.strip(),
                            findings.strip(),
                            int(duration_minutes),
                            performed_by.strip(),
                        ),
                    )

                    conn.commit()
                    st.success("Log perawatan berhasil disimpan.")
                    st.rerun()

                except Exception as e:
                    st.error(f"Gagal menyimpan log: {e}")

                finally:
                    conn.close()

st.divider()
st.subheader("Riwayat Perawatan")

if logs.empty:
    st.info("Belum ada log perawatan yang tercatat.")
else:
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Log", len(logs))

    with col2:
        st.metric(
            "Total Durasi (Jam)",
            round(logs["Durasi (Menit)"].sum() / 60, 2),
        )

    keyword = st.text_input(
        "Cari berdasarkan mesin, pekerjaan, atau teknisi"
    )

    if keyword:
        columns_to_search = [
            "Kode Aset",
            "Nama Mesin",
            "Pekerjaan",
            "Teknisi",
        ]

        mask = pd.Series(False, index=logs.index)

        for column in columns_to_search:
            mask |= logs[column].astype(str).str.contains(
                keyword,
                case=False,
                na=False,
            )

        logs = logs[mask]

    st.dataframe(
        logs,
        use_container_width=True,
        hide_index=True,
    )
