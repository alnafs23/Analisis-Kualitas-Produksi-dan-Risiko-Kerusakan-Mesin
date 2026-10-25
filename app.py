
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Manufacturing Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "maintenance.db"

st.markdown("""
<style>
    .block-container {
        padding-top: 1.6rem;
        padding-bottom: 2rem;
    }
    [data-testid="stMetric"] {
        background: var(--secondary-background-color);
        padding: 18px;
        border: 1px solid rgba(128,128,128,0.20);
        border-radius: 12px;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 14px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    if not DB_PATH.exists():
        return pd.DataFrame()

    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT * FROM machine_data", conn
        )


df = load_data()

if df.empty:
    st.error(
        "Data belum ditemukan. Jalankan database.py terlebih dahulu."
    )
    st.stop()


st.sidebar.title("Manufacturing Analytics")
st.sidebar.caption("Machine Failure Analysis")
st.sidebar.divider()

st.sidebar.subheader("Filter Data")

machine_types = sorted(df["machine_type"].dropna().unique())

selected_types = st.sidebar.multiselect(
    "Tipe produk/mesin",
    options=machine_types,
    default=machine_types,
)

failure_status = st.sidebar.selectbox(
    "Status kegagalan",
    ["Semua", "Gagal", "Tidak gagal"],
)

min_wear = int(df["tool_wear_min"].min())
max_wear = int(df["tool_wear_min"].max())

wear_range = st.sidebar.slider(
    "Rentang keausan alat (menit)",
    min_value=min_wear,
    max_value=max_wear,
    value=(min_wear, max_wear),
)

filtered = df[
    df["machine_type"].isin(selected_types)
    & df["tool_wear_min"].between(
        wear_range[0], wear_range[1]
    )
].copy()

if failure_status == "Gagal":
    filtered = filtered[filtered["machine_failure"] == 1]
elif failure_status == "Tidak gagal":
    filtered = filtered[filtered["machine_failure"] == 0]

st.sidebar.divider()
st.sidebar.caption(
    "Sumber: AI4I 2020 Predictive Maintenance Dataset"
)

st.title("Manufacturing Operations Analytics")
st.write(
    "Dashboard untuk mengeksplorasi catatan kegagalan "
    "dan parameter operasional pada dataset manufaktur."
)

if filtered.empty:
    st.warning(
        "Tidak ada data yang sesuai dengan filter. "
        "Silakan ubah pilihan filter di sidebar."
    )
    st.stop()

total_records = len(filtered)
failed_records = int(filtered["machine_failure"].sum())
normal_records = total_records - failed_records
failure_rate = failed_records / total_records * 100

st.subheader("Ringkasan Operasional")

k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Catatan", f"{total_records:,}")
k2.metric("Catatan Gagal", f"{failed_records:,}")
k3.metric("Catatan Tidak Gagal", f"{normal_records:,}")
k4.metric("Tingkat Kegagalan", f"{failure_rate:.2f}%")

st.caption(
    "Angka di atas mengikuti filter aktif. Setiap baris merupakan "
    "catatan produk, bukan identitas mesin fisik yang unik."
)


st.divider()
st.subheader("Ringkasan Temuan")

type_summary = (
    filtered.groupby("machine_type")
    .agg(
        total_records=("machine_failure", "size"),
        failed_records=("machine_failure", "sum"),
    )
    .reset_index()
)

type_summary["failure_rate_percent"] = (
    type_summary["failed_records"]
    / type_summary["total_records"]
    * 100
)

if not type_summary.empty:
    highest_type = type_summary.loc[
        type_summary["failure_rate_percent"].idxmax()
    ]

    a, b = st.columns(2)

    with a:
        st.markdown("**Tipe dengan tingkat kegagalan tertinggi**")
        st.write(
            f"Tipe **{highest_type['machine_type']}** memiliki "
            f"tingkat kegagalan **"
            f"{highest_type['failure_rate_percent']:.2f}%** "
            f"pada data yang sedang ditampilkan."
        )

    with b:
        st.markdown("**Proporsi catatan gagal**")
        st.write(
            f"Dari {total_records:,} catatan yang ditampilkan, "
            f"{failed_records:,} tercatat mengalami kegagalan "
            f"({failure_rate:.2f}%)."
        )

tab1, tab2, tab3 = st.tabs([
    "Ringkasan",
    "Analisis Parameter",
    "Eksplorasi Data",
])

with tab1:
    left, right = st.columns(2)

    with left:
        st.subheader("Tingkat Kegagalan per Tipe")

        fig_type = px.bar(
            type_summary.sort_values(
                "failure_rate_percent", ascending=False
            ),
            x="machine_type",
            y="failure_rate_percent",
            text="failure_rate_percent",
            labels={
                "machine_type": "Tipe",
                "failure_rate_percent": "Tingkat Kegagalan (%)",
            },
        )
        fig_type.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside",
        )
        fig_type.update_layout(
            yaxis_title="Tingkat Kegagalan (%)",
            xaxis_title="Tipe",
            showlegend=False,
            margin=dict(t=25, b=20),
        )
        st.plotly_chart(fig_type, use_container_width=True)

    with right:
        st.subheader("Status Catatan")

        status_summary = pd.DataFrame({
            "Status": ["Gagal", "Tidak gagal"],
            "Jumlah": [failed_records, normal_records],
        })

        fig_status = px.pie(
            status_summary,
            names="Status",
            values="Jumlah",
            hole=0.58,
        )
        fig_status.update_traces(
            textinfo="label+percent",
        )
        fig_status.update_layout(
            showlegend=False,
            margin=dict(t=25, b=20),
        )
        st.plotly_chart(fig_status, use_container_width=True)

    st.divider()
    st.subheader("Frekuensi Label Jenis Kegagalan")

    failure_columns = ["twf", "hdf", "pwf", "osf", "rnf"]

    failure_labels = {
        "twf": "TWF — Tool Wear Failure",
        "hdf": "HDF — Heat Dissipation Failure",
        "pwf": "PWF — Power Failure",
        "osf": "OSF — Overstrain Failure",
        "rnf": "RNF — Random Failure",
    }

    failure_summary = pd.DataFrame({
        "Jenis Kegagalan": [
            failure_labels[c] for c in failure_columns
        ],
        "Jumlah Label": [
            int(filtered[c].sum()) for c in failure_columns
        ],
    }).sort_values("Jumlah Label", ascending=True)

    fig_failure = px.bar(
        failure_summary,
        x="Jumlah Label",
        y="Jenis Kegagalan",
        orientation="h",
        text="Jumlah Label",
    )
    fig_failure.update_layout(
        xaxis_title="Jumlah catatan berlabel",
        yaxis_title="",
        margin=dict(l=10, r=20, t=20, b=20),
    )
    st.plotly_chart(fig_failure, use_container_width=True)

    st.caption(
        "Catatan: satu baris dapat memiliki lebih dari satu label "
        "kegagalan. Jumlah label tidak sama dengan jumlah catatan "
        "unik yang mengalami kegagalan."
    )

# =========================
# TAB 2: ANALISIS PARAMETER
# =========================
with tab2:
    st.subheader("Distribusi Keausan Alat")

    wear_fig = px.histogram(
        filtered,
        x="tool_wear_min",
        color="machine_failure",
        barmode="overlay",
        opacity=0.75,
        nbins=30,
        labels={
            "tool_wear_min": "Keausan alat (menit)",
            "machine_failure": "Kegagalan",
        },
        color_discrete_map={
            0: "#4C78A8",
            1: "#E45756",
        },
    )
    wear_fig.update_layout(
        legend_title="Kegagalan (0 = tidak, 1 = ya)",
        yaxis_title="Jumlah catatan",
    )
    st.plotly_chart(wear_fig, use_container_width=True)

    left, right = st.columns(2)

    with left:
        st.subheader("Torque berdasarkan Status")

        torque_fig = px.box(
            filtered,
            x="machine_failure",
            y="torque_nm",
            color="machine_failure",
            labels={
                "machine_failure": "Kegagalan (0 = tidak, 1 = ya)",
                "torque_nm": "Torque (Nm)",
            },
            color_discrete_map={
                0: "#4C78A8",
                1: "#E45756",
            },
        )
        torque_fig.update_layout(showlegend=False)
        st.plotly_chart(torque_fig, use_container_width=True)

    with right:
        st.subheader("Kecepatan Rotasi dan Torque")

        scatter_fig = px.scatter(
            filtered,
            x="rotational_speed_rpm",
            y="torque_nm",
            color="machine_failure",
            opacity=0.65,
            labels={
                "rotational_speed_rpm": "Kecepatan rotasi (rpm)",
                "torque_nm": "Torque (Nm)",
                "machine_failure": "Kegagalan",
            },
            color_discrete_map={
                0: "#4C78A8",
                1: "#E45756",
            },
        )
        st.plotly_chart(scatter_fig, use_container_width=True)

    st.divider()
    st.subheader("Korelasi Antarparameter Numerik")

    numeric_columns = [
        "air_temperature_k",
        "process_temperature_k",
        "rotational_speed_rpm",
        "torque_nm",
        "tool_wear_min",
        "machine_failure",
    ]

    correlation = filtered[numeric_columns].corr()

    corr_fig = px.imshow(
        correlation,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        labels={"color": "Korelasi"},
    )
    corr_fig.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(corr_fig, use_container_width=True)

    st.caption(
        "Korelasi menunjukkan hubungan statistik, bukan bukti "
        "bahwa suatu parameter menyebabkan kegagalan."
    )

with tab3:
    st.subheader("Tabel Data")
    st.write(
        "Gunakan filter di sidebar untuk mempersempit data. "
        "Klik judul kolom pada tabel untuk mengurutkan."
    )

    display_columns = [
        "udi",
        "product_id",
        "machine_type",
        "air_temperature_k",
        "process_temperature_k",
        "rotational_speed_rpm",
        "torque_nm",
        "tool_wear_min",
        "machine_failure",
    ]

    st.dataframe(
        filtered[display_columns],
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        f"Menampilkan {len(filtered):,} dari {len(df):,} "
        "catatan sesuai filter."
    )

    csv_data = filtered.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Unduh data hasil filter (CSV)",
        data=csv_data,
        file_name="machine_analysis.csv",
        mime="text/csv",
    )
