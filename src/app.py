import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
from shapely.geometry import Point, box
import os
import io

# Import local modules
from utils import calculate_bbox_from_center, calculate_zoom_level, calculate_resolution
from tile_fetcher import stitch_tiles
from geotiff_utils import save_geotiff

# --- Configuration & Translatons ---
st.set_page_config(page_title="TerraClip", layout="wide")

# Translations
TRANSLATIONS = {
    "English": {
        "title": "🌏 TerraClip",
        "desc": "This tool allows you to generate high-resolution map images from vector data.",
        "settings": "⚙️ Settings",
        "scale": "Scale (1:x)",
        "scale_help": "e.g., 10000 for 1:10000",
        "width": "Width (cm)",
        "height": "Height (cm)",
        "dpi": "DPI",
        "dpi_help": "Dots Per Inch for printing",
        "upload_label": "Upload Vector Data",
        "file_uploaded": "File uploaded: {}",
        "batch_output": "📂 Batch Output",
        "output_dir": "Output Directory",
        "filename_col": "Filename Column",
        "filename_col_help": "Column to use for filenames. Uses index if not found.",
        "error_no_latlon": "Could not find Latitude/Longitude columns in CSV",
        "error_loading": "Error loading file: {}",
        "data_preview": "📍 Data Preview",
        "select_feature": "Select Feature to Clip",
        "info_adjust": "Ensure the red box covers your area of interest. Drag map to adjust center.",
        "print_area": "Print Area",
        "center_marker": "Center",
        "manual_adjust": "Manual Center Adjustment",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "generate_btn": "Generate Map Image",
        "fetching_msg": "Fetching and stitching tiles...",
        "result_caption": "Result ({}x{} px)",
        "download_btn": "Download Image",
        "batch_processing": "📦 Batch Processing",
        "batch_desc": "Generate images for ALL points in the file.",
        "start_batch": "Start Batch Processing",
        "processing_status": "Processing {}/{}...",
        "batch_complete": "Batch processing complete!",
        "batch_saved": "Saved {} images to {}",
        "batch_failed": "Failed to process {}: {}",
        "upload_prompt": "Please upload a file to start.",
        "map_source": "Map Source",
        "api_key": "Tianditu API Key (TK)",
        "zoom_offset": "Quality Boost (Zoom Offset)",
        "zoom_offset_help": "Increase zoom level for sharper images (slower download)",
        "output_path_hint": "Files will be saved to: {}",
        "draw_geometry": "Draw Geometry on Image (Point/Polygon)",
        "draw_geometry_help": "Overlay the vector shape onto the final map image",
        "draw_label": "Show Label (Name)",
        "draw_label_help": "Draw the feature name near the center",
        "format_label": "Output Format",
        "crs_label": "Coordinate System (GeoTIFF only)",
        "crs_help": "WGS84/CGCS2000 (Lat/Lon) or WebMercator (Meters)",
        "download_geotiff": "Download GeoTIFF"
    },
    "中文": {
        "title": "🌏 TerraClip (大地裁剪师)",
        "desc": "此工具允许您根据矢量数据生成高分辨率地图图像。",
        "settings": "⚙️ 设置",
        "scale": "比例尺 (1:x)",
        "scale_help": "例如，10000 代表 1:10000",
        "width": "宽度 (cm)",
        "height": "高度 (cm)",
        "dpi": "分辨率 (DPI)",
        "dpi_help": "打印分辨率 Dots Per Inch",
        "upload_label": "上传矢量数据",
        "file_uploaded": "文件已上传: {}",
        "batch_output": "📂 批量输出",
        "output_dir": "输出目录",
        "filename_col": "文件名列",
        "filename_col_help": "CSV/SHP中用作文件名的列名。若未找到则使用索引。",
        "error_no_latlon": "CSV中未找到经纬度列 (Latitude/Longitude)",
        "error_loading": "加载文件错误: {}",
        "data_preview": "📍 数据预览",
        "select_feature": "选择要裁剪的要素",
        "info_adjust": "确保红框覆盖您感兴趣的区域。拖动地图以调整中心。",
        "print_area": "打印区域",
        "center_marker": "中心",
        "manual_adjust": "手动中心调整",
        "latitude": "纬度",
        "longitude": "经度",
        "generate_btn": "生成地图图片",
        "fetching_msg": "正在获取并拼接切片...",
        "result_caption": "结果 ({}x{} px)",
        "download_btn": "下载图片",
        "batch_processing": "📦 批量处理",
        "batch_desc": "为文件中所有点位生成图片。",
        "start_batch": "开始批量处理",
        "processing_status": "正在处理 {}/{}...",
        "batch_complete": "批量处理完成！",
        "batch_saved": "已保存 {} 张图片至 {}",
        "batch_failed": "处理失败 {}: {}",
        "upload_prompt": "请上传文件以开始。",
        "map_source": "地图源",
        "api_key": "天地图 API 密钥 (TK)",
        "zoom_offset": "清晰度增强 (Zoom Offset)",
        "zoom_offset_help": "增加缩放级别以获得更清晰的图像 (会增加下载时间)",
        "output_path_hint": "文件将保存到: {}",
        "draw_geometry": "在图片上绘制几何图形 (点/面)",
        "draw_geometry_help": "将矢量形状叠加绘制到最终的地图图片上",
        "draw_label": "显示标签 (Name)",
        "draw_label_help": "在中心点附近绘制要素名称",
        "format_label": "输出格式",
        "crs_label": "坐标系 (仅 GeoTIFF)",
        "crs_help": "WGS84/CGCS2000 (经纬度) 或 WebMercator (米)",
        "download_geotiff": "下载 GeoTIFF"
    }
}

# Language Selector
st.sidebar.header("Language / 语言")
language_option = st.sidebar.radio("Select Language / 选择语言", ["中文", "English"])

t = TRANSLATIONS[language_option]

st.title(t["title"])
st.markdown(t["desc"])

# Sidebar settings
with st.sidebar:
    st.header(t["settings"])
    
    # Scale Input
    scale = st.number_input(t["scale"], value=10000, step=1000, help=t["scale_help"])
    
    # Physical Size
    col1, col2 = st.columns(2)
    with col1:
        width_cm = st.number_input(t["width"], value=3.5, step=0.1)
    with col2:
        height_cm = st.number_input(t["height"], value=3.5, step=0.1)
    
    # Map Source
    st.divider()
    map_source = st.selectbox(t["map_source"], ["Google Satellite", "TianDiTu Satellite (天地图)"])
    
    source_code = "google"
    api_key_input = ""
    
    if "TianDiTu" in map_source:
        source_code = "tianditu"
        api_key_input = st.text_input(t["api_key"], type="password", help="Required for TianDiTu")
        if not api_key_input:
            st.warning("⚠️ TianDiTu requires an API Key!")
    
    # Quality / Zoom Offset
    zoom_offset = st.number_input(t["zoom_offset"], value=0, min_value=0, max_value=3, help=t["zoom_offset_help"])
    
    # Output Format & CRS
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        out_fmt = st.selectbox(t["format_label"], ["PNG", "GeoTIFF"])
    with col_f2:
        target_crs_name = st.selectbox(t["crs_label"], ["WebMercator (EPSG:3857)", "WGS84 (EPSG:4326)", "CGCS2000 (EPSG:4490)"], disabled=(out_fmt=="PNG"), help=t["crs_help"])
        
    # Map map CRS name to EPSG code
    crs_map = {
        "WebMercator (EPSG:3857)": "EPSG:3857",
        "WGS84 (EPSG:4326)": "EPSG:4326",
        "CGCS2000 (EPSG:4490)": "EPSG:4490" # Rasterio needs a defined EPSG. If 4490 not found, we might fallback to 4326 as they are similar.
    }
    target_crs_code = crs_map[target_crs_name]

    # Draw Geometry Toggle
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        draw_geometry = st.checkbox(t["draw_geometry"], value=True, help=t["draw_geometry_help"])
    with col_d2:
        draw_label = st.checkbox(t["draw_label"], value=True, help=t["draw_label_help"])
        
    dpi = st.number_input(t["dpi"], value=300, step=50, help=t["dpi_help"])
    
    st.divider()
    
    uploaded_file = st.file_uploader(t["upload_label"], type=["csv", "zip", "kml", "geojson"])
    
    if uploaded_file:
         st.success(t["file_uploaded"].format(uploaded_file.name))
    
    st.divider()
    st.header(t["batch_output"])
    output_dir = st.text_input(t["output_dir"], value="output")
    st.caption(t["output_path_hint"].format(os.path.abspath(output_dir)))
    filename_col = st.text_input(t["filename_col"], value="name", help=t["filename_col_help"])

def load_data(uploaded_file):
    if uploaded_file is None:
        return None
    
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    try:
        if file_ext == '.csv':
            df = pd.read_csv(uploaded_file)
            # Try to find lat/lon columns
            lat_col = next((col for col in df.columns if 'lat' in col.lower()), None)
            lon_col = next((col for col in df.columns if 'lon' in col.lower() or 'lng' in col.lower()), None)
            
            if lat_col and lon_col:
                 gdf = gpd.GeoDataFrame(
                    df, geometry=gpd.points_from_xy(df[lon_col], df[lat_col]), crs="EPSG:4326"
                )
                 return gdf
            else:
                st.error(t["error_no_latlon"])
                return None
                
        elif file_ext in ['.zip', '.kml', '.geojson', '.json']:
            # For zip (shapefile), we need to save it temporarily
            with open(f"temp_{uploaded_file.name}", "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            gdf = gpd.read_file(f"temp_{uploaded_file.name}")
            
            # Ensure CRS is EPSG:4326
            if gdf.crs is not None and gdf.crs.to_string() != "EPSG:4326":
                gdf = gdf.to_crs("EPSG:4326")
                
            return gdf
            
    except Exception as e:
        st.error(t["error_loading"].format(e))
        return None

gdf = load_data(uploaded_file)

if gdf is not None:
    st.subheader(t["data_preview"])
    st.dataframe(gdf.drop(columns='geometry').head())
    
    # Feature Selection
    feature_indices = gdf.index.tolist()
    selected_index = st.selectbox(t["select_feature"], feature_indices)
    
    if selected_index is not None:
        selected_feature = gdf.loc[selected_index]
        geometry = selected_feature.geometry
        
        # Determine center point for the NEW selection
        if geometry.geom_type == 'Point':
            new_c_lon = geometry.x
            new_c_lat = geometry.y
        else:
            centroid = geometry.centroid
            new_c_lon = centroid.x
            new_c_lat = centroid.y
            
        # Update session state if selection changed or not set
        if 'last_selected_index' not in st.session_state or st.session_state.last_selected_index != selected_index:
             st.session_state.center_lat = new_c_lat
             st.session_state.center_lon = new_c_lon
             st.session_state.last_selected_index = selected_index
             # Rerun to update map center immediately
             st.rerun()

        # Use session state for center
        center_lat = st.session_state.center_lat
        center_lon = st.session_state.center_lon

        # UI for adjusting center (Fine-tuning)
        st.info(t["info_adjust"])
        
        # Calculate BBox based on settings
        west, south, east, north = calculate_bbox_from_center(center_lat, center_lon, width_cm, height_cm, scale)
        
        # Display Map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=15, tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', attr='Google Satellite')
        
        # Draw the target bbox
        folium.Rectangle(
            bounds=[[south, west], [north, east]],
            color="red",
            weight=2,
            fill=False,
            popup=t["print_area"]
        ).add_to(m)
        
        # Draw the center point
        folium.Marker([center_lat, center_lon], popup=t["center_marker"]).add_to(m)
        
        st_data = st_folium(m, width=800, height=500)
        
        # Update center from map interaction if changed
        if st_data and st_data.get("last_object_clicked_tooltip") != t["center_marker"]:
             if st_data.get("center"):
                 new_center = st_data["center"]
                 # Logic for update if needed
                 pass

        # Manual Center Adjustment
        with st.expander(t["manual_adjust"]):
             new_lat = st.number_input(t["latitude"], value=center_lat, format="%.6f")
             new_lon = st.number_input(t["longitude"], value=center_lon, format="%.6f")
             if new_lat != center_lat or new_lon != center_lon:
                 st.session_state.center_lat = new_lat
                 st.session_state.center_lon = new_lon
                 st.rerun()

        # Generate Button
        if st.button(t["generate_btn"]):
            with st.spinner(t["fetching_msg"]):
                # Calculate BBox again with current center (in case it changed)
                west, south, east, north = calculate_bbox_from_center(center_lat, center_lon, width_cm, height_cm, scale)
                # Calculate resolution
                res = calculate_resolution(scale, dpi)
                base_zoom = calculate_zoom_level(center_lat, res)
                final_zoom = base_zoom + zoom_offset
                
                st.write(f"Base Zoom: {base_zoom}, Final Zoom: {final_zoom}, Source: {source_code}")
                
                # Fetch Image
                target_w_px = int((width_cm / 2.54) * dpi)
                target_h_px = int((height_cm / 2.54) * dpi)
                
                geometry_to_draw = geometry if draw_geometry else None
                
                # Get Label Text
                label_text = ""
                if draw_label:
                    if filename_col in selected_feature:
                        label_text = str(selected_feature[filename_col])
                    elif "name" in selected_feature:
                        label_text = str(selected_feature["name"])

                # Fetch Image
                final_img, metadata = stitch_tiles(
                    (west, south, east, north), 
                    final_zoom, 
                    (target_w_px, target_h_px),
                    source=source_code,
                    api_key=api_key_input,
                    overlay_geometry=geometry_to_draw,
                    overlay_text=label_text
                )
                
                # Display Result
                st.image(final_img, caption=t["result_caption"].format(target_w_px, target_h_px), use_column_width=False)
                
                # Download Button
                if out_fmt == "PNG":
                    buf = io.BytesIO()
                    final_img.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    
                    st.download_button(
                        label=t["download_btn"],
                        data=byte_im,
                        file_name=f"map_clip_{scale}_{zoom_offset}.png",
                        mime="image/png"
                    )
                else:
                    # GeoTIFF Download
                    # Streamlit download button expects bytes.
                    # We need to write rasterio to memory? Rasterio MemoryFile.
                    with rasterio.MemoryFile() as memfile:
                         # We need a temp path or use MemoryFile as destination.
                         # geotiff_utils.save_geotiff takes a path. 
                         # Let's write to a temporary file then read bytes.
                         tmp_path = "temp_download.tif"
                         save_geotiff(final_img, tmp_path, metadata, target_crs=target_crs_code)
                         
                         with open(tmp_path, "rb") as f:
                             byte_im = f.read()
                             
                         st.download_button(
                            label=t["download_geotiff"],
                            data=byte_im,
                            file_name=f"map_clip_{scale}_{target_crs_code.replace(':','')}.tif",
                            mime="image/tiff"
                        )
                         # Cleanup
                         if os.path.exists(tmp_path):
                             os.remove(tmp_path)

    st.divider()
    st.header(t["batch_processing"])
    st.write(t["batch_desc"])
    
    if st.button(t["start_batch"]):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total = len(gdf)
        for idx, row in gdf.iterrows():
            status_text.text(t["processing_status"].format(idx+1, total))
            
            # Determine geometry center
            geom = row.geometry
            if geom.geom_type == 'Point':
                c_lon, c_lat = geom.x, geom.y
            else:
                centroid = geom.centroid
                c_lon, c_lat = centroid.x, centroid.y
            
            # Use specified column for filename or index
            # Use specified column for filename or index
            if filename_col in row:
                fname = f"{row[filename_col]}"
            else:
                fname = f"point_{idx}"
            
            # Sanitize filename
            fname = "".join(c for c in fname if c.isalnum() or c in (' ', '.', '_', '-')).strip()
            save_path = os.path.join(output_dir, fname)
            
            # Calculate BBox
            b_west, b_south, b_east, b_north = calculate_bbox_from_center(c_lat, c_lon, width_cm, height_cm, scale)
            
            # Fetch
            res = calculate_resolution(scale, dpi)
            base_zoom = calculate_zoom_level(c_lat, res)
            final_zoom = base_zoom + zoom_offset
            
            target_w_px = int((width_cm / 2.54) * dpi)
            target_h_px = int((height_cm / 2.54) * dpi)
            
            geometry_to_draw = geom if draw_geometry else None
            
            # Get Label Text
            label_text = ""
            if draw_label:
                if filename_col in row:
                    label_text = str(row[filename_col])
                elif "name" in row:
                    label_text = str(row["name"])

            try:
                img, metadata = stitch_tiles(
                    (b_west, b_south, b_east, b_north), 
                    final_zoom, 
                    (target_w_px, target_h_px),
                    source=source_code,
                    api_key=api_key_input,
                    overlay_geometry=geometry_to_draw,
                    overlay_text=label_text
                )
                
                # Save Logic
                if out_fmt == "PNG":
                    save_path = os.path.join(output_dir, f"{fname}.png")
                    img.save(save_path)
                else:
                    save_path = os.path.join(output_dir, f"{fname}.tif")
                    save_geotiff(img, save_path, metadata, target_crs=target_crs_code)
                    
                batch_count += 1
            except Exception as e:
                st.error(t["batch_failed"].format(fname, e))
            
            progress_bar.progress((idx + 1) / total)
            
        status_text.text(t["batch_complete"])
        st.success(t["batch_saved"].format(total, os.path.abspath(output_dir)))

else:
    st.info(t["upload_prompt"])
