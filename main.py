import os
import pymupdf
import shutil
from io import BytesIO
from PIL import Image, ImageChops, ImageEnhance
import numpy as np
import time


class PDFComparer:

  def __init__(self,
               old_documents_dir,
               new_documents_dir,
               output_dir,
               quality=4.0):
    self.old_documents_dir = old_documents_dir
    self.new_documents_dir = new_documents_dir
    self.output_dir = output_dir
    self.zoom_x = quality
    self.zoom_y = quality

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
    """
    tint_color_rgba = tint_color + (255,)
    for y in range(img.height):
      for x in range(img.width):
        if img.getpixel((x,y)) == 255:
          img_rgba.putpixel((x,y), tint_color_rgba)
        else:
          img_rgba.putpixel((x,y), (0,0,0,0))
    """
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

      old_image_pil = Image.frombytes("RGB",
                                      [old_image.width, old_image.height],
                                      old_image.samples)
      new_image_pil = Image.frombytes("RGB",
                                      [new_image.width, new_image.height],
                                      new_image.samples)

      combined_image = self.overlay_images(old_image_pil,
                                           new_image_pil,
                                           tint_color=(255, 0, 0),
                                           opacity=0.5)

      if combined_image is not None:
        differences_found = True

        img_byte_array = BytesIO()
        combined_image.save(img_byte_array, format="PNG")
        img_byte_array.seek(0)

        page = output_doc.new_page(width=old_image.width,
                                   height=old_image.height)

        page.insert_image(page.rect,
                          stream=img_byte_array,
                          keep_proportion=True)

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
        print(
            f"New file corresponding to {old_file} not found in {self.new_documents_dir}"
        )
        continue

      print(
          f"Comparing {old_file} with its new version ({index + 1}/{len(old_files)})..."
      )

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

  comparer = PDFComparer(OLD_DOCUMENT_DIR, NEW_DOCUMENT_DIR, OUTPUT_DIR)
  comparer.run_comparison()
