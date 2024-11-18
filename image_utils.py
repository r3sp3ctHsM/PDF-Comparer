# My Project
# Copyright (C) 2024 Ryan Lacadin
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pymupdf
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageEnhance
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
  
  def annotate_text_differences(self, image, word_diffs, font_size):
    """Annotate word-level text differences on an image"""
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("Arial.ttf", int(font_size))
    current_x_position = {}
    
    for word, bbox in word_diffs:
      if word.startswith('+ '):
        text_color = (0, 204, 0)
        word_text = word[2:]
      elif word.startswith('- '):
        text_color = (204, 0, 0)
        word_text = word[2:]
        
      text_pos_x = float(bbox[0]) * self.quality
      text_pos_y = float(bbox[1]) * self.quality
      
      if text_pos_y in current_x_position:
        last_x_position = current_x_position[text_pos_y]
        if last_x_position + font.getbbox(" ")[2] > text_pos_x:
          arrow_text = " >"
          arrow_width = font.getbbox(arrow_text)[2]
          draw.text((last_x_position, text_pos_y), arrow_text, font=font, fill=(0,0,0))
          text_pos_x = last_x_position + arrow_width + font.getbbox(" ")[2]
          
      draw.text((text_pos_x, text_pos_y - font_size), word_text, font=font, fill=text_color)
      current_x_position[text_pos_y] = text_pos_x + font.getbbox(word_text)[2]
