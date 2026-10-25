
import streamlit as st
import pandas as pd

from database.connection import get_connection

st.set_page_config(
    page_title="Laporan Kerusakan | MIMS",
    layout="wide",
)

st.title("Laporan Kerusakan Mesin")
st.write("Catat dan pantau laporan kerusakan mesin produksi.")

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
finally:
    conn.close()

if assets.empty:
    st.warning(
        "Belum ada aset. Tambahkan aset terlebih dahulu "
        "melalui halaman Manajemen Aset."
    )
else:
    with st.form("form_laporan_kerusakan"):
        asset_options = {
            f"{row.asset_code} - {row.asset_name}": row.id
            for row in assets.itertuples(index=False)
        }

        selected_asset = st.selectbox(
            "Mesin yang mengalami kerusakan",
            list(asset_options.keys()),
        )

        title = st.text_input(
            "Judul laporan",
            placeholder="Contoh: Mesin berhenti beroperasi",
        )

        description = st.text_area(
            "Deskripsi kerusakan",
            placeholder="Jelaskan masalah yang ditemukan.",
        )

        col1, col2 = st.columns(2)

        with col1:
            reported_by = st.text_input(
                "Pelapor",
                placeholder="Nama pelapor",
            )

        with col2:
            priority = st.selectbox(
                "Prioritas",
                ["Rendah", "Sedang", "Tinggi", "Kritis"],
                index=1,
            )

        submitted = st.form_submit_button(
            "Simpan Laporan",
            use_container_width=True,
        )

        if submitted:
            if not title.strip() or not reported_by.strip():
                st.error(
                    "Judul laporan dan nama pelapor wajib diisi."
                )
            else:
                conn = get_connection()

                try:
                    conn.execute(
                        """
                        INSERT INTO failure_reports
                        (
                            asset_id,
                            reported_by,
                            title,
                            description,
                            priority
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            asset_options[selected_asset],
                            reported_by.strip(),
                            title.strip(),
                            description.strip(),
                            priority,
                        ),
                    )

                    conn.commit()
                    st.success("Laporan kerusakan berhasil disimpan.")
                    st.rerun()

                except Exception as e:
                    st.error(f"Gagal menyimpan laporan: {e}")

                finally:
                    conn.close()

st.divider()
st.subheader("Daftar Laporan Kerusakan")

conn = get_connection()

try:
    reports = pd.read_sql_query(
        """
        SELECT
            fr.id AS ID,
            a.asset_code AS 'Kode Aset',
            a.asset_name AS 'Nama Mesin',
            fr.title AS 'Judul Laporan',
            fr.reported_by AS Pelapor,
            fr.priority AS Prioritas,
            fr.status AS Status,
            fr.reported_at AS 'Waktu Laporan'
        FROM failure_reports fr
        JOIN assets a ON a.id = fr.asset_id
        ORDER BY fr.id DESC
        """,
        conn,
    )
finally:
    conn.close()

st.dataframe(
    reports,
    use_container_width=True,
    hide_index=True,
)

st.caption(f"Total laporan: {len(reports)}")
