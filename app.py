import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Point
from io import BytesIO

st.set_page_config(page_title="Mapping Project ke STO", layout="centered")
st.title("📍 Mapping Project Polygon ke Area STO")

# Upload STO dari CSV
uploaded_sto_csv = st.file_uploader("📄 Upload CSV STO (berisi kolom WKT dan Nama ODC)", type=["csv"])

# Upload Polygon Project KML
uploaded_project_file = st.file_uploader("📦 Upload Polygon Project (.kml)", type=["kml"])

if uploaded_sto_csv and uploaded_project_file:
    try:
        # Baca STO dari CSV
        df_sto = pd.read_csv(uploaded_sto_csv, sep=",", quotechar='"')
        df_sto["geometry"] = df_sto["Polygon dalam Format WKT"].apply(wkt.loads)
        gdf_sto = gpd.GeoDataFrame(df_sto, geometry="geometry", crs="EPSG:4326")

        # Baca KML project
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

        # Download Excel
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
