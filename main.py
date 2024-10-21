import os
import pymupdf
import shutil
from io import BytesIO
from PIL import Image, ImageChops, ImageEnhance
import numpy as np
import time
import difflib

# Required libraries:
# pip install pymupdf pillow numpy


class PDFComparer:

  def __init__(self, old_documents_dir, new_documents_dir, output_dir, quality=2.0, margin_offset=72):
    self.old_documents_dir = old_documents_dir
    self.new_documents_dir = new_documents_dir
    self.output_dir = output_dir
    self.zoom_x = quality
    self.zoom_y = quality
    self.margin_offset = margin_offset # Y-coordinate offset for document border

    # Ensure output directory exists
    os.makedirs(self.output_dir, exist_ok=True)

    self.clear_output_folder()

  def clear_output_folder(self):
    for filename in os.listdir(self.output_dir):
      file_path = os.path.join(self.output_dir, filename)
      try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
          os.unlink(file_path)
        elif os.path.isdir(file_path):
          shutil.rmtree(file_path)
      except Exception as e:
        print(f'Failed to delete {file_path}. Reason: {e}')

  def get_pdf_files(self, directory):
    return [f for f in os.listdir(directory) if f.endswith('.pdf')]

  def create_binary_diff_image(self, img1, img2):
    diff = ImageChops.difference(img1, img2)

    binary_diff = diff.convert("L").point(lambda p: 255 if p > 0 else 0)

    return binary_diff

  def tint_image(self, img, tint_color):
    img_rgba = Image.new("RGBA", img.size)

    img_data = np.array(img)

    img_rgba_data = np.zeros((img_data.shape[0], img_data.shape[1], 4),
                             dtype=np.uint8)
    img_rgba_data[img_data == 255] = tint_color + (255, )
    img_rgba_data[img_data == 0] = (0, 0, 0, 0)

    img_rgba = Image.fromarray(img_rgba_data, mode="RGBA")

    return img_rgba

  def overlay_images(self, img1, img2, tint_color=(255, 0, 0), opacity=1):

    binary_diff = self.create_binary_diff_image(img1, img2)

    if binary_diff.getbbox() is None:
      return None

    diff_tinted = self.tint_image(binary_diff, tint_color)

    alpha = diff_tinted.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    diff_tinted.putalpha(alpha)

    img1_rgba = img1.convert("RGBA")

    combined = Image.alpha_composite(img1_rgba, diff_tinted)
    return combined

  def render_page_to_image(self, page):
    mat = pymupdf.Matrix(self.zoom_x, self.zoom_y)
    pix = page.get_pixmap(matrix=mat)
    return pix

  def extract_text(self, page):
    words = page.get_text("words")
    lines = {}
    for word in words:
      line_key = word[3]
      if line_key not in lines:
        lines[line_key] = []
      lines[line_key].append({
        "text": word[4],
        "bbox": word[:4]
      })
    return lines

  def compare_text(self, old_text_with_positions, new_text_with_positions):
    word_diffs = []
    for line_key in set(old_text_with_positions.keys()).union(new_text_with_positions.keys()):
      old_line = old_text_with_positions.get(line_key, [])
      new_line = new_text_with_positions.get(line_key, [])

      old_text = [word["text"] for word in old_line]
      new_text = [word["text"] for word in new_line]

      diff = list(difflib.ndiff(old_text, new_text))

      old_index = 0
      new_index = 0
      for word in diff:
        if word.startswith("+ "):
          if new_index < len(new_line):
            word_diffs.append((word, new_line[new_index]["bbox"], "add"))
          new_index += 1
        elif word.startswith("- "):
          if old_index < len(old_line):
            word_diffs.append((word, old_line[old_index]["bbox"], "remove"))
          old_index += 1
        else:
          old_index += 1
          new_index += 1

    return word_diffs
  
  def compare_pdfs(self, old_file_path, new_file_path):
    old_doc = pymupdf.open(old_file_path)
    new_doc = pymupdf.open(new_file_path)
    output_doc = pymupdf.open()  #Create a new PDF for the output

    differences_found = False

    for page_num in range(min(len(old_doc), len(new_doc))):
      old_page = old_doc.load_page(page_num)
      new_page = new_doc.load_page(page_num)

      old_image = self.render_page_to_image(old_page)
      new_image = self.render_page_to_image(new_page)

      old_image_pil = Image.frombytes("RGB", [old_image.width, old_image.height], old_image.samples)
      new_image_pil = Image.frombytes("RGB", [new_image.width, new_image.height], new_image.samples)

      combined_image = self.overlay_images(old_image_pil, new_image_pil, tint_color=(240, 240, 0), opacity=0.4)

      old_text_with_positions = self.extract_text(old_page)
      new_text_with_positions = self.extract_text(new_page)
      word_diffs = self.compare_text(old_text_with_positions, new_text_with_positions)

      if combined_image is not None or word_diffs:
        differences_found = True

        if combined_image is not None:
          img_byte_array = BytesIO()
          combined_image.save(img_byte_array, format="PNG")
          img_byte_array.seek(0)

        page = output_doc.new_page(width=old_image.width, height=old_image.height)
        if combined_image is not None:
          page.insert_image(page.rect, stream=img_byte_array, keep_proportion=True)

        if word_diffs:
          font_size = 8 * self.zoom_y
          offset = font_size * 2
          current_x_position = {}
          for word, bbox, change_type in word_diffs:
            if word.startswith('+ '):
              text_color = (0,0.8,0)
              word_text = word[2:]
            elif word.startswith('- '):
              text_color = (0.9,0,0)
              word_text = word[2:]

            text_width = pymupdf.get_text_length(word_text, fontsize=font_size)

            text_pos_x = float(bbox[0]) * self.zoom_x
            text_pos_y = float(bbox[1]) * self.zoom_y

            if text_pos_y in current_x_position:
              last_x_position = current_x_position[text_pos_y]
              if last_x_position + pymupdf.get_text_length(" ", fontsize=font_size) > text_pos_x:
                arrow_text = " >"
                arrow_width = pymupdf.get_text_length(arrow_text, fontsize=font_size)
                arrow_rect = pymupdf.Rect(last_x_position, text_pos_y - font_size, last_x_position + arrow_width, text_pos_y + offset)
                page.insert_textbox(arrow_rect, arrow_text, fontsize=font_size, color=(0,0,0))
                text_pos_x = last_x_position + arrow_width + pymupdf.get_text_length(" ", fontsize=font_size)
            
            text_rect = pymupdf.Rect(text_pos_x, text_pos_y - font_size, text_pos_x + text_width, text_pos_y + offset)

            if not text_rect.is_infinite and not text_rect.is_empty:
              page.insert_textbox(text_rect, word_text, fontsize=font_size, color=text_color)
              current_x_position[text_pos_y] = text_pos_x + text_width

        if combined_image is not None:
          del combined_image
          del img_byte_array

    if differences_found:
      return output_doc
    else:
      output_doc.close()
      return None

  def run_comparison(self):
    old_files = self.get_pdf_files(self.old_documents_dir)
    new_files = self.get_pdf_files(self.new_documents_dir)

    if not old_files:
      print(f"No PDF files found in {self.old_documents_dir}")
      return

    if not new_files:
      print(f"No PDF files found in {self.new_documents_dir}")
      return

    total_start_time = time.time()

    for index, old_file in enumerate(old_files):
      old_file_path = os.path.join(self.old_documents_dir, old_file)
      new_file_path = os.path.join(self.new_documents_dir, old_file)

      if not os.path.exists(new_file_path):
        print(f"New file corresponding to {old_file} not found in {self.new_documents_dir}")
        continue

      print(f"Comparing {old_file} with its new version ({index + 1}/{len(old_files)})...")

      start_time = time.time()
      output_doc = self.compare_pdfs(old_file_path, new_file_path)
      end_time = time.time()
      elapsed_time = end_time - start_time
      if output_doc:
        output_file_path = os.path.join(self.output_dir, f"diff_{old_file}")
        output_doc.save(output_file_path)
        output_doc.close()
        print(f"Differences found: {output_file_path}")
      else:
        print(f"No differences found for {old_file}.")

      print(f"Time take for {old_file}: {elapsed_time:.2f} seconds\n")

    total_end_time = time.time()
    total_elapsed_time = total_end_time - total_start_time

    print(
        f"Total time taken for comparing all documents: {total_elapsed_time:.2f} seconds"
    )


if __name__ == "__main__":
  OLD_DOCUMENT_DIR = "./Old_Documents"
  NEW_DOCUMENT_DIR = "./New_Documents"
  OUTPUT_DIR = "./Output"
  MARGIN_OFFSET = 72

  comparer = PDFComparer(OLD_DOCUMENT_DIR, NEW_DOCUMENT_DIR, OUTPUT_DIR, margin_offset=MARGIN_OFFSET)
  comparer.run_comparison()
