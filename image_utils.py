import pymupdf
from PIL import Image, ImageChops, ImageEnhance
import numpy as np

class ImageUtils:

  def __init__(self, quality):
    self.quality = quality
  
  def render_page_to_image(self, page):
    """Render the page at a higher resolution using the zoom factor."""
    mat = pymupdf.Matrix(self.quality, self.quality)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img

  def create_binary_diff_image(self, img1, img2):
    """Create a binary difference image where differences are white and no differences are black."""
    # Find the differences between the images
    diff = ImageChops.difference(img1, img2)

    # Convert the difference image to grayscale and then to binery using a threshold
    binary_diff = diff.convert("L").point(lambda p: 255 if p > 0 else 0)

    return binary_diff

  def tint_image(self, img, tint_color):
    """Apply a color tint to a binery image where white is the tine color and black is transparent."""
    # Create a new image with the same size as the binary image
    img_rgba = Image.new("RGBA", img.size)

    # Create a numpy array from the binary image
    img_data = np.array(img)

    # Create a mask where white pixels in the binary image are set to the tint color and black pixels are transparent
    mask = img_data == 255
    
    img_rgba_data = np.zeros((img_data.shape[0], img_data.shape[1], 4), dtype=np.uint8)
    img_rgba_data[mask] = tint_color + (255,)
    img_rgba_data[~mask] = (0, 0, 0, 0)

    # Convert the numpy array back to an image
    img_rgba = Image.fromarray(img_rgba_data, mode="RGBA")

    return img_rgba

  def overlay_differences(self, img1, img2, tint_color=(255, 0, 0), opacity=0.5):
    """Overlay differences between img2 and img1 with the specified color tint and opacity."""
    # Create the binary difference image
    binary_diff = self.create_binary_diff_image(img1, img2)

    # Check if there are any differences
    if binary_diff.getbbox() is None:
      return None

    # Apply the tint color to the binary difference image
    diff_tinted = self.tint_image(binary_diff, tint_color)

    # Apply the opacity to the tinted difference image
    alpha = diff_tinted.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    diff_tinted.putalpha(alpha)

    # Composite the tinted difference on top of the base image without affecting the brightness
    img1_rgba = img1.convert("RGBA")
    combined = Image.alpha_composite(img1_rgba, diff_tinted)
    return combined

  def render_pages_to_images(self, old_page, new_page):
    """Render PDF pages to images."""
    old_image = self.render_page_to_image(old_page)
    new_image = self.render_page_to_image(new_page)
    return old_image, new_image