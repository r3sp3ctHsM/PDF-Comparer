import os
import pymupdf
import shutil
import cv2
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance


class PDFComparer:
  def __init__(self, old_documents_dir, new_documents_dir, output_dir):
    self.old_documents_dir = old_documents_dir
    self.new_documents_dir = new_documents_dir
    self.output_dir = output_dir

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

  def highlight_differences(self, img1, img2):
    diff = ImageChops.difference(img1, img2)
    diff = ImageEnhance.Contrast(diff).enhance(2)
    diff = diff.convert("L") # Convert to grayscale

    np_diff = np.array(diff)
    _, thresh = cv2.threshold(np_diff, 50, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
      highlighted_img = img1.copy()
      draw = ImageDraw.Draw(highlighted_img)
      bbox_list = []

      for contour in contours:
        x,y,w,h = cv2.boundingRect(contour)
        bbox_list.append((x,y,x+w,y+h))
        draw.rectangle([x,y,x+w,y+h], outline="red", width=2)

      return highlighted_img, bbox_list    
    return None, None

  def render_page_to_image(self, page):
    if hasattr(page, "get_pixmap"):
      return page.get_pixmap()
    elif hasattr(page, "getPixmap"):
      return page.getPixmap()
    else:
      raise AttributeError("The page object does not have a method to render to an image.")
  
  def compare_pdfs(self, old_file_path, new_file_path):
    old_doc = pymupdf.open(old_file_path)
    new_doc = pymupdf.open(new_file_path)
    output_doc = pymupdf.open() #Create a new PDF for the output

    differences_found = False

    for page_num in range(min(len(old_doc), len(new_doc))):
      old_page = old_doc.load_page(page_num)
      new_page = new_doc.load_page(page_num)

      old_image = self.render_page_to_image(old_page)
      new_image = self.render_page_to_image(new_page)

      old_image_pil = Image.frombytes("RGB", [old_image.width, old_image.height], old_image.samples)
      new_image_pil = Image.frombytes("RGB", [new_image.width, new_image.height], new_image.samples)

      highlighted_img, bbox_list = self.highlight_differences(old_image_pil, new_image_pil)
      if highlighted_img:
        differences_found = True
        for bbox in bbox_list:
          rect = pymupdf.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
          highlight = old_page.add_rect_annot(rect)
          highlight.set_colors(stroke=(1,0,0))
          highlight.update()

      output_doc.insert_pdf(old_doc, from_page=page_num, to_page=page_num)

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

    for old_file in old_files:
      old_file_path = os.path.join(self.old_documents_dir, old_file)
      new_file_path = os.path.join(self.new_documents_dir, old_file)

      if not os.path.exists(new_file_path):
        print(f"New file corresponding to {old_file} not found in {self.new_documents_dir}")
        continue

      print(f"Comparing {old_file} with its new version.")
      output_doc = self.compare_pdfs(old_file_path, new_file_path)
      if output_doc:
        output_file_path = os.path.join(self.output_dir, f"diff_{old_file}")
        output_doc.save(output_file_path)
        output_doc.close()
      else:
        print(f"No differences found for {old_file}.")

    print("Comparison Complete")

if __name__ == "__main__":
  OLD_DOCUMENT_DIR = "./Old_Documents"
  NEW_DOCUMENT_DIR = "./New_Documents"
  OUTPUT_DIR = "./Output"

  comparer = PDFComparer(OLD_DOCUMENT_DIR, NEW_DOCUMENT_DIR, OUTPUT_DIR)
  comparer.run_comparison()