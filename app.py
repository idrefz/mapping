import streamlit as st
import pandas as pd
import geopandas as gpd
import os
from shapely import wkt
from shapely.geometry import Polygon
from shapely.errors import WKTReadingError
from io import BytesIO

st.set_page_config(page_title="Mapping Polygon ke STO", layout="wide")
st.title("📍 Mapping Beberapa File Polygon (.kml) ke Area STO")

# Fungsi memperbaiki WKT tidak tertutup
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

# Upload Excel STO
uploaded_sto = st.file_uploader("📄 Upload Excel STO (berisi kolom WKT & Nama ODC)", type=["xlsx"])

# Multi-upload KML
uploaded_kmls = st.file_uploader("📦 Upload Beberapa File Polygon Project (.kml)", type=["kml"], accept_multiple_files=True)

if uploaded_sto and uploaded_kmls:
    try:
        # Gabungkan semua file KML
        gdfs = []
        for file in uploaded_kmls:
            try:
                gdf = gpd.read_file(file, driver="KML")
                gdf["source_file"] = file.name
                gdfs.append(gdf)
            except Exception as e:
                st.warning(f"⚠️ Gagal membaca {file.name}: {e}")

        if not gdfs:
            st.error("❌ Tidak ada file KML valid.")
            st.stop()

        gdf_all = pd.concat(gdfs, ignore_index=True)
        gdf_all = gdf_all.to_crs(epsg=4326)

        # Baca dan perbaiki WKT dari STO
        df_sto = pd.read_excel(uploaded_sto)
        df_sto["Fixed WKT"] = df_sto["Polygon dalam Format WKT"].apply(fix_wkt)
        df_sto = df_sto[df_sto["Fixed WKT"].notnull()]
        df_sto["geometry"] = df_sto["Fixed WKT"].apply(wkt.loads)
        gdf_sto = gpd.GeoDataFrame(df_sto, geometry="geometry", crs="EPSG:4326")

        # Mapping
        gdf_joined = gpd.sjoin(gdf_all, gdf_sto, predicate='within', how='left')
        gdf_joined["centroid"] = gdf_joined.geometry.centroid
        gdf_joined["latitude"] = gdf_joined.centroid.y
        gdf_joined["longitude"] = gdf_joined.centroid.x

        output_df = gdf_joined[["Name", "ODC", "latitude", "longitude", "source_file"]]
        output_df.columns = ["Nama Project", "Nama STO", "Latitude", "Longitude", "File KML"]

        st.success(f"✅ Mapping selesai. Total: {len(output_df)} data.")
        st.dataframe(output_df)

        # Download hasil
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
