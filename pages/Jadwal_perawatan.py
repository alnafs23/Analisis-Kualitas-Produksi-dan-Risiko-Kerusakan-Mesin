
import streamlit as st
import pandas as pd

from datetime import date, timedelta
from database.connection import get_connection

st.set_page_config(
    page_title="Jadwal Perawatan | MIMS",
    layout="wide",
)

st.title("Jadwal Preventive Maintenance")
st.write("Kelola jadwal perawatan berkala mesin produksi.")

# Ambil daftar aset dan jadwal yang sudah ada
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

    schedules = pd.read_sql_query(
        """
        SELECT
            ms.id,
            a.asset_code AS 'Kode Aset',
            a.asset_name AS 'Nama Mesin',
            ms.schedule_name AS 'Nama Perawatan',
            ms.maintenance_type AS 'Jenis Perawatan',
            ms.interval_days AS 'Interval (Hari)',
            ms.last_maintenance_date AS 'Perawatan Terakhir',
            ms.next_maintenance_date AS 'Perawatan Berikutnya',
            ms.assigned_to AS 'Penanggung Jawab',
            ms.status AS Status
        FROM maintenance_schedules ms
        JOIN assets a ON a.id = ms.asset_id
        ORDER BY ms.next_maintenance_date ASC
        """,
        conn,
    )
finally:
    conn.close()

# Form jadwal baru
st.subheader("Tambah Jadwal Perawatan")

if assets.empty:
    st.warning(
        "Belum ada aset. Tambahkan aset melalui halaman Manajemen Aset."
    )
else:
    with st.form("form_jadwal_perawatan"):
        asset_options = {
            f"{row.asset_code} - {row.asset_name}": row.id
            for row in assets.itertuples(index=False)
        }

        selected_asset = st.selectbox(
            "Pilih mesin",
            list(asset_options.keys()),
        )

        schedule_name = st.text_input(
            "Nama perawatan",
            placeholder="Contoh: Pemeriksaan motor penggerak",
        )

        maintenance_type = st.selectbox(
            "Jenis perawatan",
            [
                "Pemeriksaan",
                "Pelumasan",
                "Pembersihan",
                "Penggantian Komponen",
                "Kalibrasi",
                "Lainnya",
            ],
        )

        interval_days = st.number_input(
            "Interval perawatan (hari)",
            min_value=1,
            max_value=365,
            value=30,
            step=1,
        )

        last_date = st.date_input(
            "Tanggal perawatan terakhir",
            value=date.today(),
        )

        assigned_to = st.text_input(
            "Penanggung jawab",
            placeholder="Nama teknisi atau tim",
        )

        submitted = st.form_submit_button(
            "Simpan Jadwal",
            use_container_width=True,
        )

        if submitted:
            if not schedule_name.strip():
                st.error("Nama perawatan wajib diisi.")
            else:
                next_date = last_date + timedelta(
                    days=int(interval_days)
                )

                conn = get_connection()

                try:
                    conn.execute(
                        """
                        INSERT INTO maintenance_schedules (
                            asset_id,
                            schedule_name,
                            maintenance_type,
                            interval_days,
                            last_maintenance_date,
                            next_maintenance_date,
                            assigned_to,
                            status
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            asset_options[selected_asset],
                            schedule_name.strip(),
                            maintenance_type,
                            int(interval_days),
                            str(last_date),
                            str(next_date),
                            assigned_to.strip(),
                            "Aktif",
                        ),
                    )

                    conn.commit()
                    st.success(
                        f"Jadwal berhasil disimpan. "
                        f"Perawatan berikutnya: {next_date:%d-%m-%Y}"
                    )
                    st.rerun()

                except Exception as e:
                    st.error(f"Gagal menyimpan jadwal: {e}")

                finally:
                    conn.close()

st.divider()

# Daftar jadwal
st.subheader("Daftar Jadwal Perawatan")

if schedules.empty:
    st.info("Belum ada jadwal perawatan.")
else:
    today = date.today()

    def get_schedule_status(value, saved_status):
        if saved_status != "Aktif":
            return saved_status

        try:
            due_date = date.fromisoformat(str(value)[:10])

            if due_date < today:
                return "Terlambat"
            if due_date == today:
                return "Jatuh Tempo Hari Ini"
            return "Terjadwal"

        except (ValueError, TypeError):
            return "Tanggal Tidak Valid"

    schedules["Kondisi Jadwal"] = schedules.apply(
        lambda row: get_schedule_status(
            row["Perawatan Berikutnya"],
            row["Status"],
        ),
        axis=1,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Jadwal", len(schedules))

    with col2:
        overdue = (
            schedules["Kondisi Jadwal"] == "Terlambat"
        ).sum()
        st.metric("Jadwal Terlambat", int(overdue))

    with col3:
        due_today = (
            schedules["Kondisi Jadwal"] == "Jatuh Tempo Hari Ini"
        ).sum()
        st.metric("Jatuh Tempo Hari Ini", int(due_today))

    st.dataframe(
        schedules.drop(columns=["id"]),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Perbarui Status Jadwal")

    schedule_options = {
        (
            f"#{row['id']} — {row['Nama Mesin']} — "
            f"{row['Nama Perawatan']}"
        ): row["id"]
        for _, row in schedules.iterrows()
    }

    selected_schedule = st.selectbox(
        "Pilih jadwal",
        list(schedule_options.keys()),
    )

    with st.form("form_status_jadwal"):
        new_status = st.selectbox(
            "Status jadwal",
            ["Aktif", "Ditangguhkan", "Selesai"],
        )

        update = st.form_submit_button("Perbarui Status")

        if update:
            conn = get_connection()

            try:
                conn.execute(
                    """
                    UPDATE maintenance_schedules
                    SET status = ?
                    WHERE id = ?
                    """,
                    (
                        new_status,
                        schedule_options[selected_schedule],
                    ),
                )

                conn.commit()
                st.success("Status jadwal berhasil diperbarui.")
                st.rerun()

            except Exception as e:
                st.error(f"Gagal memperbarui jadwal: {e}")

            finally:
                conn.close()
