import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Polygon
from shapely.errors import WKTReadingError
from io import BytesIO

st.set_page_config(page_title="Mapping Project ke STO", layout="centered")
st.title("📍 Mapping Project Polygon ke Area STO")

# Upload STO dari Excel
uploaded_sto_excel = st.file_uploader("📄 Upload Excel STO (berisi kolom WKT dan Nama ODC)", type=["xlsx"])

# Upload Polygon Project KML
uploaded_project_file = st.file_uploader("📦 Upload Polygon Project (.kml)", type=["kml"])

# Fungsi untuk memperbaiki WKT
def fix_wkt(wkt_str):
    try:
        geom = wkt.loads(wkt_str)
        if isinstance(geom, Polygon):
            coords = list(geom.exterior.coords)
            if coords[0] != coords[-1]:
                coords.append(coords[0])
                geom = Polygon(coords)
        return geom.wkt
    except Exception:
        return None

# Jika file STO diunggah
if uploaded_sto_excel:
    df_sto_raw = pd.read_excel(uploaded_sto_excel)

    # Tombol perbaikan WKT otomatis
    if st.button("🔧 Perbaiki WKT Otomatis"):
        df_sto_raw["Fixed WKT"] = df_sto_raw["Polygon dalam Format WKT"].apply(fix_wkt)
        df_fixed = df_sto_raw[df_sto_raw["Fixed WKT"].notnull()].copy()

        st.success(f"Berhasil diperbaiki: {len(df_fixed)} baris")
        st.dataframe(df_fixed)

        # Unduh hasil perbaikan
        output_wkt = BytesIO()
        with pd.ExcelWriter(output_wkt, engine="xlsxwriter") as writer:
            df_fixed.to_excel(writer, index=False, sheet_name="WKT Diperbaiki")
        st.download_button(
            "⬇️ Download Hasil WKT Diperbaiki",
            data=output_wkt.getvalue(),
            file_name="ODC_WKT_Diperbaiki.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Jika kedua file diunggah
if uploaded_sto_excel and uploaded_project_file:
    try:
        # Baca file Excel STO
        df_sto = pd.read_excel(uploaded_sto_excel)
        df_sto["Fixed WKT"] = df_sto["Polygon dalam Format WKT"].apply(fix_wkt)
        df_sto = df_sto[df_sto["Fixed WKT"].notnull()]
        df_sto["geometry"] = df_sto["Fixed WKT"].apply(wkt.loads)
        gdf_sto = gpd.GeoDataFrame(df_sto, geometry="geometry", crs="EPSG:4326")

        # Baca file KML project
        gdf_project = gpd.read_file(uploaded_project_file, driver="KML").to_crs(epsg=4326)

        # Spatial join
        gdf_joined = gpd.sjoin(gdf_project, gdf_sto, predicate='within', how='left')
        gdf_joined["centroid"] = gdf_joined.geometry.centroid
        gdf_joined["latitude"] = gdf_joined.centroid.y
        gdf_joined["longitude"] = gdf_joined.centroid.x

        # Output
        output_df = gdf_joined[["Name", "ODC", "latitude", "longitude"]]
        output_df.columns = ["Nama Project", "Nama STO", "Latitude", "Longitude"]

        st.success("🎉 Mapping selesai!")
        st.dataframe(output_df)

        # Unduh hasil mapping
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            output_df.to_excel(writer, index=False, sheet_name="Hasil Mapping")
        st.download_button(
            "⬇️ Download Hasil Excel",
            data=output.getvalue(),
            file_name="hasil_mapping.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Terjadi error: {e}")
