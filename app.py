import streamlit as st
import geopandas as gpd
import pandas as pd
from shapely import wkt
from shapely.geometry import Polygon
from io import BytesIO
import zipfile
import os

st.set_page_config(page_title="📍 Mapping Polygon ke STO", layout="centered")
st.title("📍 Mapping Project Polygon ke Area STO (Auto-Fix + ZIP)")

def fix_geometry(geom):
    try:
        if geom.is_valid:
            return geom
        fixed = geom.buffer(0)
        return fixed if fixed.is_valid else geom
    except Exception:
        return geom

# Upload STO Excel
sto_file = st.file_uploader("📄 Upload Excel STO (berisi kolom WKT dan Nama ODC)", type=["xlsx"])

# Upload ZIP berisi banyak KML
zip_file = st.file_uploader("📦 Upload ZIP File Polygon Project (.kml)", type=["zip"])

if sto_file and zip_file:
    try:
        # === BACA STO ===
        df_sto = pd.read_excel(sto_file)
        df_sto["geometry"] = df_sto["Polygon dalam Format WKT"].apply(wkt.loads)
        gdf_sto = gpd.GeoDataFrame(df_sto, geometry="geometry", crs="EPSG:4326")

        # === EKSTRAK & BACA SEMUA KML ===
        with zipfile.ZipFile(zip_file, "r") as z:
            kml_files = [f for f in z.namelist() if f.endswith(".kml") and not "/._" in f and not f.startswith("__MACOSX")]
            gdfs = []
            for file in kml_files:
                with z.open(file) as f:
                    try:
                        gdf = gpd.read_file(f, driver="KML")
                        gdf["source_file"] = os.path.basename(file)
                        gdf["geometry"] = gdf["geometry"].apply(fix_geometry)
                        gdfs.append(gdf)
                    except Exception as e:
                        st.warning(f"⚠️ Gagal membaca {file}: {e}")

        if not gdfs:
            st.error("Tidak ada file .kml yang berhasil diproses.")
        else:
            gdf_project = pd.concat(gdfs, ignore_index=True).set_crs("EPSG:4326")

            # === SPATIAL JOIN ===
            gdf_joined = gpd.sjoin(gdf_project, gdf_sto, predicate="within", how="left")
            gdf_joined["centroid"] = gdf_joined.geometry.centroid
            gdf_joined["latitude"] = gdf_joined.centroid.y
            gdf_joined["longitude"] = gdf_joined.centroid.x

            # === OUTPUT ===
            output_df = gdf_joined[["Name", "ODC", "latitude", "longitude", "source_file"]]
            output_df.columns = ["Nama Project", "Nama STO", "Latitude", "Longitude", "File Asal"]
            st.success("🎉 Mapping selesai! Berikut sebagian hasilnya:")
            st.dataframe(output_df.head())

            # === DOWNLOAD EXCEL ===
            out_xlsx = BytesIO()
            with pd.ExcelWriter(out_xlsx, engine="xlsxwriter") as writer:
                output_df.to_excel(writer, index=False, sheet_name="Hasil Mapping")
            st.download_button(
                "⬇️ Download Hasil Excel",
                data=out_xlsx.getvalue(),
                file_name="hasil_mapping_polygon_ke_sto.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ Terjadi error saat memproses: {e}")
