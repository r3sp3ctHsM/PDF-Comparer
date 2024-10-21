import pymupdf
from PIL import Image, ImageChops, ImageEnhance
import numpy as np

def render_page_to_image(page, zoom_x, zoom_y):
  """Render the page at a higher resolution using the zoom factor."""
  mat = pymupdf.Matrix(zoom_x, zoom_y)
  pix = page.get_pixmap(matrix=mat)
  return pix

def create_binary_diff_image(img1, img2):
  """Create a binary difference image where differences are white and no differences are black."""
  # Find the differences between the images
  diff = ImageChops.difference(img1, img2)

  # Convert the difference image to grayscale and then to binery using a threshold
  binary_diff = diff.convert("L").point(lambda p: 255 if p > 0 else 0)

  return binary_diff

def tint_image(img, tint_color):
  """Apply a color tint to a binery image where white is the tine color and black is transparent."""
  # Create a new image with the same size as the binary image
  img_rgba = Image.new("RGBA", img.size)

  # Create a numpy array from the binary image
  img_data = np.array(img)

  # Create a mask where white pixels in the binary image are set to the tint color and black pixels are transparent
  img_rgba_data = np.zeros((img_data.shape[0], img_data.shape[1], 4), dtype=np.uint8)
  img_rgba_data[img_data == 255] = tint_color + (255,)
  img_rgba_data[img_data == 0] = (0, 0, 0, 0)

  # Convert the numpy array back to an image
  img_rgba = Image.fromarray(img_rgba_data, mode="RGBA")

  return img_rgba

def overlay_differences(img1, img2, tint_color=(255, 0, 0), opacity=0.5):
  """Overlay differences between img2 and img1 with the specified color tint and opacity."""
  # Create the binary difference image
  binary_diff = create_binary_diff_image(img1, img2)

  # Check if there are any differences
  if binary_diff.getbbox() is None:
    return None

  # Apply the tint color to the binary difference image
  diff_tinted = tint_image(binary_diff, tint_color)

  # Apply the opacity to the tinted difference image
  alpha = diff_tinted.split()[3]
  alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
  diff_tinted.putalpha(alpha)

  # Composite the tinted difference on top of the base image without affecting the brightness
  img1_rgba = img1.convert("RGBA")
  combined = Image.alpha_composite(img1_rgba, diff_tinted)
  return combined