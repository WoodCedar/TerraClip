# 🌏 TerraClip / 地图裁剪

> **Precision Satellite Imagery for Field Surveys & Research**
> **专为牛马野外设计的卫星地图切片工具**

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**TerraClip** is a lightweight, local web tool that solves a specific pain point in GIS workflows: **"I need a satellite map image of valid physical size (e.g., 3.5cm) at a specific scale (e.g., 1:10,000) centered on my vector data."**

**TerraClip** 是一个轻量级的 GIS 工具，解决了野外工作中一个痛点需求：**“我需要一张以我的矢量数据为中心，特定物理尺寸（如 3.5cm）和特定比例尺（如 1:10,000）的卫星地图图片。”**

---

## ✨ Key Features / 核心功能

*   **🗺️ Dual Sources / 双底图**: Supports **Google Satellite** (Global) & **TianDiTu** (China). 支持 Google 卫星图与天地图（需 Key）。
*   **📏 Precise Scaling / 精确比例**: Input Scale (1:x) + Physical Dimensions (cm) + DPI = Pixel Perfect Output.
*   **📐 Vector Clipping / 矢量裁剪**: Upload **SHP, KML, GeoJSON, CSV**. Auto-centers on features.
*   **💾 GeoTIFF Support / 空间坐标**: Output **GeoTIFF** with EPSG:3857, WGS84, or CGCS2000 projections.
*   **📦 Batch Processing / 批量处理**: One-click generation for hundreds of points/polygons.
*   **✏️ Overlays / 标注绘制**: Auto-draw feature geometry and labels (Names) on the image.

## Installation / 安装

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/map-clipper.git
    cd map-clipper
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage / 使用方法

1.  Run the application:
    ```bash
    streamlit run src/app.py
    ```

2.  Open your browser (usually `http://localhost:8501`).
3.  Upload your vector file (`.csv`, `.zip` shapefile, `.kml`, `.geojson`).
4.  Configure scale, size, and DPI.
5.  Click **Generate** or use **Batch Processing**.

## License

MIT License.

