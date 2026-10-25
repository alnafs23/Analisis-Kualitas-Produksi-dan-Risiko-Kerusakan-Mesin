
import streamlit as st
import pandas as pd

from database.connection import get_connection

st.set_page_config(
    page_title="Work Order | MIMS",
    layout="wide",
)

st.title("Work Order")
st.write("Kelola dan pantau pekerjaan perbaikan mesin.")

conn = get_connection()

try:
    assets = pd.read_sql_query(
        """
        SELECT id, asset_code, asset_name
        FROM assets
        ORDER BY asset_code
        """,
        conn,
    )

    reports = pd.read_sql_query(
        """
        SELECT id, asset_id, title, priority
        FROM failure_reports
        WHERE status != 'Selesai'
        ORDER BY id DESC
        """,
        conn,
    )

    orders = pd.read_sql_query(
        """
        SELECT
            w.id,
            w.work_order_code AS 'Kode Work Order',
            a.asset_code AS 'Kode Aset',
            a.asset_name AS 'Nama Mesin',
            w.title AS 'Pekerjaan',
            w.assigned_to AS 'Teknisi',
            w.priority AS 'Prioritas',
            w.status AS Status,
            w.planned_date AS 'Tanggal Rencana'
        FROM work_orders w
        JOIN assets a ON a.id = w.asset_id
        ORDER BY w.id DESC
        """,
        conn,
    )
finally:
    conn.close()

st.subheader("Buat Work Order")

if assets.empty:
    st.warning(
        "Tambahkan aset terlebih dahulu melalui halaman Manajemen Aset."
    )
else:
    with st.form("form_work_order"):
        asset_options = {
            f"{row.asset_code} - {row.asset_name}": row.id
            for row in assets.itertuples(index=False)
        }

        selected_asset = st.selectbox(
            "Pilih mesin",
            list(asset_options.keys()),
        )

        related_reports = reports[
            reports["asset_id"] == asset_options[selected_asset]
        ]

        report_options = {"Tanpa laporan terkait": None}

        for row in related_reports.itertuples(index=False):
            report_options[
                f"#{row.id} - {row.title} ({row.priority})"
            ] = row.id

        selected_report = st.selectbox(
            "Laporan kerusakan terkait",
            list(report_options.keys()),
        )

        title = st.text_input(
            "Nama pekerjaan",
            placeholder="Contoh: Pemeriksaan motor penggerak",
        )

        description = st.text_area("Deskripsi pekerjaan")
        assigned_to = st.text_input("Teknisi yang ditugaskan")
        priority = st.selectbox(
            "Prioritas pekerjaan",
            ["Rendah", "Sedang", "Tinggi", "Kritis"],
            index=1,
        )
        planned_date = st.date_input("Tanggal rencana perbaikan")

        submitted = st.form_submit_button(
            "Buat Work Order",
            use_container_width=True,
        )

        if submitted:
            if not title.strip() or not assigned_to.strip():
                st.error("Nama pekerjaan dan teknisi wajib diisi.")
            else:
                conn = get_connection()

                try:
                    next_id = conn.execute(
                        """
                        SELECT COALESCE(MAX(id), 0) + 1
                        FROM work_orders
                        """
                    ).fetchone()[0]

                    code = f"WO-{next_id:04d}"

                    conn.execute(
                        """
                        INSERT INTO work_orders (
                            work_order_code,
                            asset_id,
                            failure_report_id,
                            assigned_to,
                            title,
                            description,
                            priority,
                            status,
                            planned_date
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            code,
                            asset_options[selected_asset],
                            report_options[selected_report],
                            assigned_to.strip(),
                            title.strip(),
                            description.strip(),
                            priority,
                            "Menunggu",
                            str(planned_date),
                        ),
                    )

                    conn.commit()
                    st.success(f"Work Order {code} berhasil dibuat.")
                    st.rerun()

                except Exception as e:
                    st.error(f"Gagal membuat Work Order: {e}")

                finally:
                    conn.close()

st.divider()
st.subheader("Daftar Work Order")

if orders.empty:
    st.info("Belum ada Work Order.")
else:
    st.dataframe(
        orders,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Perbarui Status Pekerjaan")

    order_options = {
        f"{row['Kode Work Order']} — {row['Pekerjaan']}": row["id"]
        for _, row in orders.iterrows()
    }

    selected_order = st.selectbox(
        "Pilih Work Order",
        list(order_options.keys()),
    )

    current_order = orders[
        orders["id"] == order_options[selected_order]
    ].iloc[0]

    statuses = [
        "Menunggu",
        "Dalam Proses",
        "Selesai",
        "Dibatalkan",
    ]

    current_status = current_order["Status"]
    status_index = (
        statuses.index(current_status)
        if current_status in statuses
        else 0
    )

    with st.form("form_update_status"):
        new_status = st.selectbox(
            "Status baru",
            statuses,
            index=status_index,
        )

        update = st.form_submit_button("Simpan Perubahan")

        if update:
            conn = get_connection()

            try:
                conn.execute(
                    """
                    UPDATE work_orders
                    SET status = ?,
                        started_at = CASE
                            WHEN ? = 'Dalam Proses'
                                 AND started_at IS NULL
                            THEN CURRENT_TIMESTAMP
                            ELSE started_at
                        END,
                        completed_at = CASE
                            WHEN ? = 'Selesai'
                            THEN CURRENT_TIMESTAMP
                            WHEN ? != 'Selesai'
                            THEN NULL
                            ELSE completed_at
                        END
                    WHERE id = ?
                    """,
                    (
                        new_status,
                        new_status,
                        new_status,
                        new_status,
                        order_options[selected_order],
                    ),
                )

                if new_status == "Selesai":
                    conn.execute(
                        """
                        UPDATE failure_reports
                        SET status = 'Selesai',
                            resolved_at = CURRENT_TIMESTAMP
                        WHERE id = (
                            SELECT failure_report_id
                            FROM work_orders
                            WHERE id = ?
                        )
                        """,
                        (order_options[selected_order],),
                    )

                conn.commit()
                st.success("Status Work Order berhasil diperbarui.")
                st.rerun()

            except Exception as e:
                st.error(f"Gagal memperbarui status: {e}")

            finally:
                conn.close()
