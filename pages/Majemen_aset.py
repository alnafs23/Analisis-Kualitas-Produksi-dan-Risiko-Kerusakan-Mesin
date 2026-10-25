
import streamlit as st
import pandas as pd

from database.connection import get_connection

st.set_page_config(
    page_title="Manajemen Aset | MIMS",
    layout="wide",
)

st.title("Manajemen Aset")
st.write("Kelola data mesin dan peralatan produksi.")

# Form tambah aset
with st.expander("Tambah Aset Baru", expanded=True):
    with st.form("form_tambah_aset"):
        col1, col2 = st.columns(2)

        with col1:
            asset_code = st.text_input(
                "Kode Aset",
                placeholder="MCH-001",
            )
            asset_name = st.text_input("Nama Mesin")
            category = st.selectbox(
                "Kategori",
                ["Produksi", "Pengemasan", "Utilitas", "Lainnya"],
            )

        with col2:
            location = st.text_input("Lokasi Mesin")
            manufacturer = st.text_input("Produsen")

        submitted = st.form_submit_button(
            "Simpan Aset",
            use_container_width=True,
        )

        if submitted:
            if not asset_code.strip() or not asset_name.strip():
                st.error("Kode aset dan nama mesin wajib diisi.")
            else:
                conn = get_connection()

                try:
                    conn.execute(
                        """
                        INSERT INTO assets
                        (asset_code, asset_name, category, location, manufacturer)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            asset_code.strip(),
                            asset_name.strip(),
                            category,
                            location.strip(),
                            manufacturer.strip(),
                        ),
                    )
                    conn.commit()
                    st.success("Aset berhasil disimpan.")
                    st.rerun()

                except Exception as e:
                    if "UNIQUE constraint failed" in str(e):
                        st.error("Kode aset sudah digunakan.")
                    else:
                        st.error(f"Aset gagal disimpan: {e}")

                finally:
                    conn.close()

st.divider()

# Daftar aset
st.subheader("Daftar Aset")

conn = get_connection()

try:
    df = pd.read_sql_query(
        """
        SELECT
            id,
            asset_code AS 'Kode Aset',
            asset_name AS 'Nama Mesin',
            category AS 'Kategori',
            location AS 'Lokasi',
            manufacturer AS 'Produsen',
            status AS 'Status'
        FROM assets
        ORDER BY id DESC
        """,
        conn,
    )
finally:
    conn.close()

keyword = st.text_input("Cari berdasarkan kode atau nama mesin")

if keyword:
    mask = (
        df["Kode Aset"].str.contains(keyword, case=False, na=False)
        | df["Nama Mesin"].str.contains(keyword, case=False, na=False)
    )
    df = df[mask]

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
)

st.caption(f"Total aset ditemukan: {len(df)}")
