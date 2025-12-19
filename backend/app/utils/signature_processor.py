"""
Signature Image Processor
Automatically removes background from signature images using Otsu's thresholding method
"""
import io
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def calculate_otsu_threshold(histogram: np.ndarray) -> int:
    """
    Calculate optimal threshold using Otsu's method
    Analyzes histogram to find the threshold that minimizes intra-class variance
    
    Args:
        histogram: Array of pixel intensity counts (256 values for grayscale)
    
    Returns:
        Optimal threshold value (0-255)
    """
    total_pixels = histogram.sum()
    
    if total_pixels == 0:
        return 128  # Default threshold
    
    # Normalize histogram
    histogram = histogram.astype(float) / total_pixels
    
    # Calculate cumulative sums
    cumsum = np.cumsum(histogram)
    cumsum_mean = np.cumsum(histogram * np.arange(256))
    
    # Global mean
    global_mean = cumsum_mean[-1]
    
    # Calculate between-class variance for all thresholds
    max_variance = 0
    optimal_threshold = 0
    
    for t in range(256):
        w0 = cumsum[t]  # Weight of class 0 (background)
        w1 = 1 - w0     # Weight of class 1 (foreground)
        
        if w0 == 0 or w1 == 0:
            continue
        
        # Mean of class 0
        mean0 = cumsum_mean[t] / w0 if w0 > 0 else 0
        # Mean of class 1
        mean1 = (global_mean - cumsum_mean[t]) / w1 if w1 > 0 else 0
        
        # Between-class variance
        variance = w0 * w1 * (mean0 - mean1) ** 2
        
        if variance > max_variance:
            max_variance = variance
            optimal_threshold = t
    
    logger.info(f"📊 Otsu's threshold calculated: {optimal_threshold}")
    return optimal_threshold


def analyze_image_histogram(image: Image.Image) -> dict:
    """
    Analyze image histogram to determine optimal processing parameters
    
    Returns:
        dict with threshold information
    """
    # Convert to grayscale
    grayscale = image.convert('L')
    
    # Get histogram
    histogram = np.array(grayscale.histogram())
    
    # Calculate Otsu's threshold
    otsu_threshold = calculate_otsu_threshold(histogram)
    
    # Adjust threshold for signatures (usually need higher threshold to capture thin strokes)
    # Add margin to preserve signature details
    adjusted_threshold = min(otsu_threshold + 30, 240)
    
    # Calculate statistics
    pixels = np.array(grayscale)
    mean_brightness = pixels.mean()
    std_brightness = pixels.std()
    
    return {
        'otsu_threshold': otsu_threshold,
        'adjusted_threshold': adjusted_threshold,
        'mean_brightness': mean_brightness,
        'std_brightness': std_brightness,
        'histogram': histogram.tolist()
    }


def remove_background_auto(image_bytes: bytes, margin: int = 20) -> bytes:
    """
    Remove background from signature image using automatic threshold detection
    
    Args:
        image_bytes: Raw image bytes
        margin: Extra margin added to threshold to preserve signature details
    
    Returns:
        PNG image bytes with transparent background
    """
    logger.info("🖼️ Processing signature image with auto threshold...")
    
    # Open image
    image = Image.open(io.BytesIO(image_bytes))
    
    # Convert to RGB if necessary
    if image.mode in ('RGBA', 'P'):
        # Create white background
        rgb_image = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'RGBA':
            rgb_image.paste(image, mask=image.split()[3])  # Use alpha channel as mask
        else:
            rgb_image.paste(image)
        image = rgb_image
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Analyze histogram and get optimal threshold
    analysis = analyze_image_histogram(image)
    threshold = analysis['adjusted_threshold']
    
    logger.info(f"📊 Image analysis: Otsu={analysis['otsu_threshold']}, Adjusted={threshold}, "
                f"Mean brightness={analysis['mean_brightness']:.1f}")
    
    # Convert to grayscale for processing
    grayscale = image.convert('L')
    
    # Convert to numpy array for processing
    img_array = np.array(image)
    gray_array = np.array(grayscale)
    
    # Create alpha channel based on threshold
    # Pixels brighter than threshold become transparent
    # Pixels darker than threshold remain visible (signature strokes)
    alpha = np.where(gray_array > threshold, 0, 255).astype(np.uint8)
    
    # Create RGBA image
    rgba_array = np.zeros((img_array.shape[0], img_array.shape[1], 4), dtype=np.uint8)
    
    # For signature strokes, use the original color (usually black/dark)
    rgba_array[:, :, 0] = img_array[:, :, 0]  # R
    rgba_array[:, :, 1] = img_array[:, :, 1]  # G
    rgba_array[:, :, 2] = img_array[:, :, 2]  # B
    rgba_array[:, :, 3] = alpha               # A
    
    # Create output image
    output_image = Image.fromarray(rgba_array, 'RGBA')
    
    # Optional: Crop to content bounds with padding
    bbox = output_image.getbbox()
    if bbox:
        padding = 10
        left = max(0, bbox[0] - padding)
        top = max(0, bbox[1] - padding)
        right = min(output_image.width, bbox[2] + padding)
        bottom = min(output_image.height, bbox[3] + padding)
        output_image = output_image.crop((left, top, right, bottom))
    
    # Save to bytes
    output_buffer = io.BytesIO()
    output_image.save(output_buffer, format='PNG', optimize=True)
    output_buffer.seek(0)
    
    logger.info(f"✅ Signature processed successfully. Output size: {output_image.size}")
    
    return output_buffer.getvalue()


def process_signature_for_upload(image_bytes: bytes, filename: str) -> tuple:
    """
    Process signature image and prepare for upload
    
    Args:
        image_bytes: Raw image bytes
        filename: Original filename
    
    Returns:
        tuple: (processed_bytes, new_filename)
    """
    # Process image
    processed_bytes = remove_background_auto(image_bytes)
    
    # Generate new filename with .png extension
    base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
    new_filename = f"{base_name}_signature.png"
    
    return processed_bytes, new_filename
