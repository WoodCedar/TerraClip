import unittest
import math
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from utils import calculate_resolution, calculate_zoom_level, calculate_bbox_from_center

class TestMapMath(unittest.TestCase):
    def test_resolution_calculation(self):
        # Scale 1:10000, DPI 300
        # 1 pixel = (1/300) inch = (1/300)*0.0254 meters
        # 1 pixel on map = ((1/300)*0.0254) * 10000 meters
        expected_res = (0.0254 / 300) * 10000
        calculated = calculate_resolution(10000, 300)
        self.assertAlmostEqual(calculated, expected_res, places=5)
        print(f"1:10000 @ 300DPI = {calculated:.4f} m/px")

    def test_zoom_calculation(self):
        # At latitude 0, resolution for zoom 0 is ~156543.03 m/px
        # If we need resolution X, zoom should be log2(156543.03 / X)
        
        # target resolution 10 m/px at equator
        target_res = 10.0
        lat = 0
        zoom = calculate_zoom_level(lat, target_res)
        
        # Expected zoom
        # 156543 / 2^z = 10
        # 2^z = 15654.3
        # z = log2(15654.3) ~ 13.93 -> ceil -> 14
        self.assertEqual(zoom, 14)
        print(f"Zoom level for 10m/px at equator = {zoom}")

    def test_bbox_calculation(self):
        # 10cm x 10cm at 1:10000
        # Real world size: 0.1m * 10000 = 1000m = 1km
        width_cm = 10
        height_cm = 10
        scale = 10000
        
        center_lat = 0
        center_lon = 0
        
        west, south, east, north = calculate_bbox_from_center(center_lat, center_lon, width_cm, height_cm, scale)
        
        # Check width in degrees
        # At equator 1 degree ~ 111319.9 m
        expected_deg_width = 1000 / 111319.9
        
        self.assertAlmostEqual(east - west, expected_deg_width, places=4)
        self.assertAlmostEqual(north - south, expected_deg_width, places=4) # at equator lat/lon degrees are same size
        print(f"BBox width in degrees: {east-west:.6f}")

if __name__ == '__main__':
    unittest.main()
