
import streamlit as st
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from io import BytesIO
import fiona

st.set_page_config(page_title="Mapping Project ke STO", layout="centered")
st.title("📍 Mapping Project Polygon ke Area STO")

DEFAULT_STO_FILE = "sto_default.geojson"

with st.expander("🔁 Upload Ulang File STO (.kml) jika Perlu"):
    uploaded_sto_file = st.file_uploader("Upload KML STO (opsional, kalau ada perubahan)", type=["kml"])
    if uploaded_sto_file:
        try:
            layers = fiona.listlayers(uploaded_sto_file)
            st.write("✅ Layer ditemukan:", layers)
            gdf_list = []
            for layer in layers:
                try:
                    gdf = gpd.read_file(uploaded_sto_file, driver="KML", layer=layer)
                    gdf["Nama_STO"] = layer
                    gdf_list.append(gdf)
                except Exception as e:
                    st.warning(f"⚠️ Gagal baca layer {layer}: {e}")
            if gdf_list:
                gdf_sto = pd.concat(gdf_list, ignore_index=True)
                gdf_sto.to_file(DEFAULT_STO_FILE, driver="GeoJSON")
                st.success("✅ Semua layer berhasil digabung dan disimpan sebagai default!")
            else:
                st.error("❌ Tidak ada layer yang berhasil dibaca.")
        except Exception as e:
            st.error(f"Gagal konversi: {e}")

try:
    gdf_sto = gpd.read_file(DEFAULT_STO_FILE)
    st.info("📁 File STO terdeteksi dan siap digunakan.")
except:
    st.warning("⚠️ Belum ada file STO default. Silakan upload dulu.")
    gdf_sto = gpd.GeoDataFrame()

uploaded_project_file = st.file_uploader("📦 Upload Polygon Project (.kml)", type=["kml"])

if uploaded_project_file and not gdf_sto.empty:
    try:
        gdf_project = gpd.read_file(uploaded_project_file, driver="KML")
        gdf_sto = gdf_sto.to_crs(epsg=4326)
        gdf_project = gdf_project.to_crs(epsg=4326)
        gdf_joined = gpd.sjoin(gdf_project, gdf_sto, predicate='within', how='left')
        gdf_joined["centroid"] = gdf_joined.geometry.centroid
        gdf_joined["latitude"] = gdf_joined.centroid.y
        gdf_joined["longitude"] = gdf_joined.centroid.x
        output_df = gdf_joined[["Name_left", "Nama_STO", "latitude", "longitude"]]
        output_df.columns = ["Nama Project", "Nama STO", "Latitude", "Longitude"]
        st.success("🎉 Mapping selesai!")
        st.dataframe(output_df)
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
        st.error(f"Terjadi error saat pemrosesan: {e}")
