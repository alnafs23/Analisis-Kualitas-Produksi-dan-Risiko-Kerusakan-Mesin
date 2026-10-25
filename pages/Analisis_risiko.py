
import streamlit as st

from analytics.risk_analysis import (
    load_data,
    get_failure_summary,
    get_failure_by_type,
    plot_failure_distribution,
    plot_failure_by_type,
    plot_failure_types,
)

st.set_page_config(
    page_title="Analisis Risiko | MIMS",
    layout="wide",
)

st.title("Analisis Risiko Kerusakan Mesin")
st.caption(
    "Analisis eksploratif menggunakan dataset sintetis AI4I 2020."
)

try:
    df = load_data()
    summary = get_failure_summary(df)

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Catatan",
        f"{summary['total_records']:,}",
    )

    col2.metric(
        "Catatan Kegagalan",
        f"{summary['failure_records']:,}",
    )

    col3.metric(
        "Tingkat Kegagalan",
        f"{summary['failure_rate']:.2f}%",
    )

    st.divider()

    st.subheader("Distribusi Kondisi Mesin")
    st.plotly_chart(
        plot_failure_distribution(df),
        use_container_width=True,
    )

    st.subheader("Tingkat Kegagalan per Tipe Mesin")
    st.plotly_chart(
        plot_failure_by_type(df),
        use_container_width=True,
    )

    st.subheader("Indikator Jenis Kegagalan")
    st.plotly_chart(
        plot_failure_types(df),
        use_container_width=True,
    )

    with st.expander("Lihat tabel tingkat kegagalan"):
        result = get_failure_by_type(df)
        result["failure_rate"] = result["failure_rate"].round(2)
        st.dataframe(
            result,
            use_container_width=True,
            hide_index=True,
        )

    st.info(
        "Tingkat kegagalan dalam dataset ini merupakan proporsi "
        "catatan yang memiliki label Machine failure = 1. "
        "Angka ini bukan estimasi probabilitas kegagalan mesin "
        "pada pabrik tertentu."
    )

except FileNotFoundError:
    st.error(
        "Dataset tidak ditemukan. Pastikan file "
        "data/ai4i2020.csv tersedia."
    )

except Exception as e:
    st.error(f"Analisis gagal dijalankan: {e}")
