import math
import mercantile
from typing import Tuple

def calculate_resolution(scale: float, dpi: int) -> float:
    """
    Calculate the required resolution in meters/pixel.
    
    Args:
        scale (float): The map scale denominator (e.g., 10000 for 1:10000).
        dpi (int): Dots per inch (e.g., 300).
        
    Returns:
        float: Resolution in meters per pixel.
    """
    # 1 inch = 0.0254 meters
    # 1 pixel = 1/dpi inches
    # 1 pixel on paper = (1/dpi) * 0.0254 meters
    # At scale 1:S, 1 unit on paper = S units in reality.
    # So 1 pixel represents: ((1/dpi) * 0.0254) * scale meters
    meters_per_pixel = (0.0254 / dpi) * scale
    return meters_per_pixel

def calculate_zoom_level(latitude: float, resolution: float) -> int:
    """
    Calculate the optimal integer zoom level for a given latitude and resolution.
    
    Args:
        latitude (float): Latitude in degrees.
        resolution (float): Desired resolution in meters/pixel.
        
    Returns:
        int: The closest integer zoom level (usually ceiling to ensure quality).
    """
    # Resolution = 156543.03392 * cos(lat) / 2^zoom
    # 2^zoom = 156543.03392 * cos(lat) / Resolution
    # zoom = log2(156543.03392 * cos(lat) / Resolution)
    
    if resolution <= 0:
        return 20 # Fallback
        
    lat_rad = math.radians(latitude)
    target_res = resolution
    
    # Earth radius at equator ~ 6378137
    # Equator circumference ~ 40075016.686
    initial_res = 156543.03392 # Resolution at zoom 0, lat 0
    
    required_zoom = math.log2((initial_res * math.cos(lat_rad)) / target_res)
    
    return math.ceil(required_zoom)

def calculate_bbox_from_center(lat: float, lon: float, width_cm: float, height_cm: float, scale: float) -> Tuple[float, float, float, float]:
    """
    Calculate the bounding box (west, south, east, north) given a center point,
    physical dimensions, and scale.
    """
    # Calculate real-world dimensions in meters
    width_m = (width_cm / 100.0) * scale
    height_m = (height_cm / 100.0) * scale
    
    # We need to convert meters to degrees.
    # Longitude degrees depend on latitude.
    # Latitude degrees are roughly constant (~111km).
    
    meters_per_degree_lat = 111319.9
    meters_per_degree_lon = 111319.9 * math.cos(math.radians(lat))
    
    delta_lat = (height_m / 2) / meters_per_degree_lat
    delta_lon = (width_m / 2) / meters_per_degree_lon
    
    west = lon - delta_lon
    east = lon + delta_lon
    south = lat - delta_lat
    north = lat + delta_lat
    
    return (west, south, east, north)

def get_pixel_dimensions(width_cm: float, height_cm: float, dpi: int) -> Tuple[int, int]:
    """
    Calculate pixel dimensions from physical size and DPI.
    """
    width_px = int((width_cm / 2.54) * dpi)
    height_px = int((height_cm / 2.54) * dpi)
    return width_px, height_px
