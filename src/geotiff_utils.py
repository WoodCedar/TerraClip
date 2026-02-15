import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import calculate_default_transform, reproject, Resampling
from PIL import Image

def save_geotiff(image: Image.Image, output_path: str, metadata: dict, target_crs: str = "EPSG:3857"):
    """
    Save a PIL Image as a GeoTIFF, optionally reprojecting it.
    
    Args:
        image: PIL Image object.
        output_path: Destination file path.
        metadata: Dictionary containing 'bounds' (west, south, east, north) in EPSG:3857 and 'crs'.
        target_crs: Target CRS string (e.g., "EPSG:3857", "EPSG:4326", "EPSG:4490").
    """
    # Convert PIL to Numpy (Channels Last -> Channels First for Rasterio)
    # PIL is (H, W, C) or (H, W). Rasterio needs (C, H, W).
    img_array = np.array(image)
    
    if len(img_array.shape) == 2: # Grayscale
        rows, cols = img_array.shape
        count = 1
        img_array = img_array.reshape(1, rows, cols)
    else: # RGB or RGBA
        rows, cols, channels = img_array.shape
        count = channels
        # Move channels to first dimension
        img_array = np.moveaxis(img_array, 2, 0)

    # Source Metadata
    src_bounds = metadata['bounds'] # (w, s, e, n)
    src_crs = metadata['crs'] # Normally EPSG:3857
    
    # Calculate Source Affine Transform
    # from_bounds(west, south, east, north, width, height)
    src_transform = from_bounds(*src_bounds, cols, rows)
    
    dst_crs = target_crs
    
    # Check if reprojection is needed
    if src_crs == dst_crs:
        # Write directly
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=rows,
            width=cols,
            count=count,
            dtype=img_array.dtype,
            crs=src_crs,
            transform=src_transform,
        ) as dst:
            dst.write(img_array)
    else:
        # Reproject
        transform, width, height = calculate_default_transform(
            src_crs, dst_crs, cols, rows, *src_bounds
        )
        
        kwargs = {
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height,
            'driver': 'GTiff',
            'count': count,
            'dtype': img_array.dtype
        }

        with rasterio.open(output_path, 'w', **kwargs) as dst:
            for i in range(1, count + 1):
                reproject(
                    source=rasterio.band(rasterio.open(
                        None, 'r', 
                        driver='GTiff', 
                        height=rows, width=cols, count=count, 
                        dtype=img_array.dtype, 
                        crs=src_crs, transform=src_transform
                    ), i), # This is a bit hacky, normally we pass array directly but reproject accepts source array
                    destination=rasterio.band(dst, i),
                    src_transform=src_transform,
                    src_crs=src_crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest
                )
            
            # Re-implementation for cleaner array handling without dummy dataset
            # Retrying the reproject call pattern more simply:
            destination_array = np.zeros((count, height, width), dtype=img_array.dtype)
            
            for i in range(count):
                reproject(
                    source=img_array[i],
                    destination=destination_array[i],
                    src_transform=src_transform,
                    src_crs=src_crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.bilinear
                )
            
            # Now write the reprojected array
            dst.write(destination_array)
