import io
import math
import requests
import mercantile
from PIL import Image
from typing import Tuple

def fetch_tile(x: int, y: int, z: int, source: str = "google", api_key: str = "") -> Image.Image:
    """
    Fetch a single tile from the specified source.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    if source == "google":
        # Google Satellite URL format
        url = f"https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
    elif source == "tianditu":
        # TianDiTu Satellite (img_w)
        # Randomize subdomains t0-t7
        subdomain = f"t{ (x + y) % 8 }"
        url = f"http://{subdomain}.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk={api_key}"
    else:
        # Fallback to Google
        url = f"https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content))
    except Exception as e:
        print(f"Error fetching tile {x},{y},{z} from {source}: {e}")
        return Image.new('RGB', (256, 256), (200, 200, 200)) # Grey for error

from shapely.geometry.base import BaseGeometry
from shapely.geometry import Point, Polygon, MultiPolygon
from PIL import ImageDraw, ImageFont

def stitch_tiles(bbox: Tuple[float, float, float, float], zoom: int, target_size: Tuple[int, int], source: str = "google", api_key: str = "", overlay_geometry: BaseGeometry = None, overlay_text: str = "") -> Tuple[Image.Image, dict]:
    """
    Fetch tiles, stitch, crop, and optionally draw the overlay geometry and text.
    Returns (Image, MetadataDict). Metadata includes 'bounds' (west, south, east, north in meters), 'crs' (EPSG code).
    """
    west, south, east, north = bbox
    target_w, target_h = target_size
    
    # ... (existing tile fetching logic is unchanged, but we need to re-include it or just hook into the end)
    # Since replace_file_content replaces the whole function if I select the whole range, 
    # I should preserve the fetching logic. 
    # To be safe and concise, I will call the original logic (if I hadn't replaced it). 
    # But here I am replacing the WHOLE function body to insert the drawing logic at the end.
    
    # Get the tile range
    tiles = list(mercantile.tiles(west, south, east, north, zoom))
    
    if not tiles:
        return Image.new('RGB', target_size, (200, 200, 200))

    # Grid bounds
    min_x = min(t.x for t in tiles)
    max_x = max(t.x for t in tiles)
    min_y = min(t.y for t in tiles)
    max_y = max(t.y for t in tiles)
    
    tile_width = max_x - min_x + 1
    tile_height = max_y - min_y + 1
    
    canvas_w = tile_width * 256
    canvas_h = tile_height * 256
    canvas = Image.new('RGB', (canvas_w, canvas_h))
    
    # Paste tiles
    for t in tiles:
        img = fetch_tile(t.x, t.y, t.z, source, api_key)
        px = (t.x - min_x) * 256
        py = (t.y - min_y) * 256
        canvas.paste(img, (px, py))
        
    # Crop Logic
    ul_tile = mercantile.ul(mercantile.Tile(x=min_x, y=min_y, z=zoom))
    canvas_west = ul_tile.lng
    canvas_north = ul_tile.lat
    
    br_tile_bounds = mercantile.bounds(mercantile.Tile(x=max_x, y=max_y, z=zoom))
    canvas_east = br_tile_bounds.east
    canvas_south = br_tile_bounds.south
    
    def get_meters(lon, lat):
        return mercantile.xy(lon, lat)
        
    c_min_x_m, c_min_y_m = get_meters(canvas_west, canvas_south)
    c_max_x_m, c_max_y_m = get_meters(canvas_east, canvas_north)
    b_min_x_m, b_min_y_m = get_meters(west, south)
    b_max_x_m, b_max_y_m = get_meters(east, north)
    
    range_x_m = c_max_x_m - c_min_x_m
    range_y_m = c_max_y_m - c_min_y_m
    
    offset_x_m = b_min_x_m - c_min_x_m
    pixel_x = int((offset_x_m / range_x_m) * canvas_w)
    
    width_m = b_max_x_m - b_min_x_m
    pixel_w = int((width_m / range_x_m) * canvas_w)
    
    offset_y_m = c_max_y_m - b_max_y_m
    pixel_y = int((offset_y_m / range_y_m) * canvas_h)
    
    height_m = b_max_y_m - b_min_y_m
    pixel_h = int((height_m / range_y_m) * canvas_h)
    
    # Initial Crop
    cropped = canvas.crop((pixel_x, pixel_y, pixel_x + pixel_w, pixel_y + pixel_h))
    
    # Resize to target
    final_img = cropped.resize(target_size, Image.LANCZOS)
    
    # --- Overlay Drawing Logic ---
    if overlay_geometry:
        draw = ImageDraw.Draw(final_img, 'RGBA')
        
        def to_img_px(lon, lat):
            # Project lat/lon to meters
            x_m, y_m = get_meters(lon, lat)
            
            # Relative to BBox Bottom-Left (b_min_x_m, b_min_y_m)
            # x_m grows East, y_m grows North
            
            rel_x_m = x_m - b_min_x_m
            rel_y_m = y_m - b_min_y_m # y_m - south
            
            # Scale to Image Size
            # Image Width covers width_m
            # Image Height covers height_m
            
            px_x = (rel_x_m / width_m) * target_w
            # Py Image Y is top-down. Map Y is bottom-up (North is High Y)
            # so 0 map y = bottom image. max map y = top image.
            # We want: max map y -> 0 image y. 0 map y -> height image y.
            # (height_m - rel_y_m) / height_m * target_h
            
            px_y = ((height_m - rel_y_m) / height_m) * target_h
            return (px_x, px_y)

        if overlay_geometry.geom_type == 'Point':
            pt = overlay_geometry
            px, py = to_img_px(pt.x, pt.y)
            # Draw a circle marker
            r = 10 # 10px radius
            color = (255, 0, 0, 180) # Red, semi-transparent
            draw.ellipse((px-r, py-r, px+r, py+r), fill=color, outline='white')
            
        elif overlay_geometry.geom_type in ['Polygon', 'MultiPolygon']:
             polys = [overlay_geometry] if overlay_geometry.geom_type == 'Polygon' else overlay_geometry.geoms
             
             for poly in polys:
                 # Exterior
                 coords = list(poly.exterior.coords)
                 px_coords = [to_img_px(c[0], c[1]) for c in coords]
                 
                 # Draw polygon
                 fill_color = (0, 0, 255, 50) # Blue, very transparent
                 outline_color = (0, 0, 255, 255) # Blue solid
                 
                 draw.polygon(px_coords, fill=fill_color, outline=outline_color)

    # --- Text Drawing Logic ---
    if overlay_text:
        draw = ImageDraw.Draw(final_img, 'RGBA')
        
        # Calculate text position (Center of image)
        # Or if we have geometry, center of geometry? 
        # For now, let's put it in the center of the image, as the image IS centered on the feature (unless dragged).
        # Better: if overlay_geometry exists, use its projected pixel centroid.
        
        text_x, text_y = target_w // 2, target_h // 2
        
        if overlay_geometry:
             if overlay_geometry.geom_type == 'Point':
                 text_x, text_y = to_img_px(overlay_geometry.x, overlay_geometry.y)
             else:
                 centroid = overlay_geometry.centroid
                 text_x, text_y = to_img_px(centroid.x, centroid.y)
        
        # Draw Text
        try:
            # Try to use a larger font if possible, but default is safe
            font = ImageFont.truetype("arial.ttf", 20) 
        except IOError:
            font = ImageFont.load_default()
            
        text = str(overlay_text)
        
        # Get text size to center it
        # draw.textbbox is newer PIL, textsize is deprecated
        if hasattr(draw, "textbbox"):
            left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
            w = right - left
            h = bottom - top
        else:
            w, h = draw.textsize(text, font=font)
        
        # Offset to center on point, maybe move it up a bit
        draw_x = text_x - w / 2
        draw_y = text_y - h - 10 # 10px above point
        
        # Draw outline/shadow for readability
        outline_color = "black"
        text_color = "white"
        
        # Box background? Or just simple text with outline
        # range(start, stop, step)
        for xo in range(-1, 2):
            for yo in range(-1, 2):
                draw.text((draw_x + xo, draw_y + yo), text, font=font, fill=outline_color)
                
        draw.text((draw_x, draw_y), text, font=font, fill=text_color)

    
    # Calculate bounds of the final cropped image in Web Mercator Meters
    # Using the same pixel logic:
    # Final West = Canvas West + (pixel_x * (range_x_m / canvas_w))
    # Final North = Canvas North - (pixel_y * (range_y_m / canvas_h)) (Y grows down in pixels, up in meters... careful with signs)
    
    # Let's be precise:
    # Canvas Top-Left (Meters): (c_min_x_m, c_max_y_m)
    # cropped_top_left_x_m = c_min_x_m + (pixel_x / canvas_w) * (c_max_x_m - c_min_x_m)
    # cropped_top_left_y_m = c_max_y_m - (pixel_y / canvas_h) * (c_max_y_m - c_min_y_m)
    
    # cropped_bottom_right_x_m = c_min_x_m + ((pixel_x + pixel_w) / canvas_w) * (range_x_m)
    # cropped_bottom_right_y_m = c_max_y_m - ((pixel_y + pixel_h) / canvas_h) * (range_y_m)
    
    final_west_m = c_min_x_m + (pixel_x / canvas_w) * range_x_m
    final_north_m = c_max_y_m - (pixel_y / canvas_h) * range_y_m
    final_east_m = c_min_x_m + ((pixel_x + pixel_w) / canvas_w) * range_x_m
    final_south_m = c_max_y_m - ((pixel_y + pixel_h) / canvas_h) * range_y_m
    
    metadata = {
        "bounds": (final_west_m, final_south_m, final_east_m, final_north_m),
        "crs": "EPSG:3857"
    }

    return final_img, metadata
