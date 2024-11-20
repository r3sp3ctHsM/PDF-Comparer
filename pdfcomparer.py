# PDF Comparer
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

import os
import time
import shutil
import json
from io import BytesIO
import pymupdf #PyMuPDF
from text_comparer import TextComparer
from image_utils import ImageUtils
import gc
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Load configuration from config.json
with open('config.json', 'r') as config_file:
  config = json.load(config_file)
  
# Set default core count if not specified by the user
if config["core_count"] is None:
  config["core_count"] = int(os.cpu_count())

@contextmanager
def open_pdf(file_path: str):
  doc = pymupdf.open(file_path)
  try:
    yield doc
  finally:
    doc.close()

class PDFComparer:
  def __init__(self,config):
    """
    Initialise PDFComparer with directories and quality settings from config.
    
    :param config: Configuration dictionary containing settings.
    """
    
    self.old_documents_dir = config["old_documents_dir"]
    self.new_documents_dir = config["new_documents_dir"]
    self.output_dir = config["output_dir"]
    self.quality = config["quality"]
    self.font_size = config["font_size"] * self.quality # Scale font size with quality
    self.core_count = config["core_count"]

    self.image_utils = ImageUtils(self.quality)
    self.text_comparer = TextComparer()

    # Ensure output directory exists
    os.makedirs(self.output_dir, exist_ok=True)
    self.clear_output_folder()
    
    self.completed_comparisons = 0
    self.lock = Lock()

  def clear_output_folder(self):
    """Clear the output folder at the start of the script."""
    for filename in os.listdir(self.output_dir):
      if filename == '.gitkeep':
        continue
      file_path = os.path.join(self.output_dir, filename)
      try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
          os.unlink(file_path)
        elif os.path.isdir(file_path):
          shutil.rmtree(file_path)
      except Exception as e:
        print(f'Failed to delete {file_path}. Reason: {e}')

  def get_pdf_files(self, directory):
    """
    Get a list of PDF files in the specified directory
    :param directory: Directory to search for PDF files
    :return: List of PDF file names"""
    return [f for f in os.listdir(directory) if f.endswith('.pdf')]
  
  def save_page_image(self, image, output_dir, page_num):
    """Save a page image to the specified output directory."""
    if not os.path.exists(output_dir):
      os.makedirs(output_dir)
    image_file_path = os.path.join(output_dir, f"page_{page_num:02d}.jpg")
    image.convert("RGB").save(image_file_path, "JPEG", quality=85)

  def compare_pdfs(self, old_file_path, new_file_path):
    """
    Compare two PDF files and return a document with differences highlighted
    :param old_file_path: Path to the old PDF file
    :param new_file_path: Path to the new PDF file
    """
    base_name = os.path.splitext(os.path.basename(old_file_path))[0]
    output_dir = os.path.join(self.output_dir, f"diff_{base_name}")
    start_time = time.time()

    with open_pdf(old_file_path) as old_doc, open_pdf(new_file_path) as new_doc:
        differences_found = False

        for page_num in range(min(len(old_doc), len(new_doc))):
            old_page = old_doc.load_page(page_num)
            new_page = new_doc.load_page(page_num)

            # Render pages to images
            old_image_pil, new_image_pil = self.image_utils.render_pages_to_images(old_page, new_page)

            # Overlay differences (image-level differences)
            overlay_image = self.image_utils.overlay_differences(
                old_image_pil, new_image_pil, tint_color=(170, 51, 106)
            )

            # Extract and compare text (word-level differences)
            word_diffs = self.text_comparer.extract_and_compare_text(old_page, new_page)

            # Combined image: Overlay + Annotated text differences
            combined_image = None
            if overlay_image or word_diffs:
                differences_found = True
                if overlay_image:
                    combined_image = overlay_image.convert("RGBA")

                if word_diffs:
                    if combined_image is None:
                        combined_image = old_image_pil.convert("RGBA")
                    self.image_utils.annotate_text_differences(
                        combined_image, word_diffs, self.font_size
                    )

            # Save the outputs
            if overlay_image:
                overlay_output_dir = os.path.join(output_dir, "overlay_differences")
                self.save_page_image(overlay_image, overlay_output_dir, page_num)
            
            if combined_image:
                combined_output_dir = os.path.join(output_dir, "combined_differences")
                self.save_page_image(combined_image, combined_output_dir, page_num)

            if word_diffs:
                word_diff_output_dir = os.path.join(output_dir, "word_differences")
                word_diff_image = old_image_pil.convert("RGBA")
                self.image_utils.annotate_text_differences(
                    word_diff_image, word_diffs, self.font_size
                )
                self.save_page_image(word_diff_image, word_diff_output_dir, page_num)

            # Cleanup to free memory
            if overlay_image:
                del overlay_image
            if combined_image:
                del combined_image
            del old_image_pil, new_image_pil
            gc.collect()

    end_time = time.time()
    elapsed_time = end_time - start_time

    with self.lock:
        if differences_found:
            print(f"Differences found: {output_dir}")
        else:
            print(f"No differences found for {output_dir}")

        print(f"Time taken for {output_dir}: {elapsed_time:.2f} seconds")

        self.completed_comparisons += 1
        print(f"Progress: {self.completed_comparisons}/{self.total_comparisons} comparisons completed\n")
  
  def run_comparison(self):
    """Run the comparison for all PDFs in the specified directories"""
    
    print("Starting PDF Comparison tool now")
    
    old_files = self.get_pdf_files(self.old_documents_dir)
    new_files = self.get_pdf_files(self.new_documents_dir)

    if not old_files:
      print(f"No PDF files found in the old documents directory: {self.old_documents_dir}")

    if not new_files:
      print(f"No PDF files found in the new documents directory: {self.new_documents_dir}")

    total_start_time = time.time()
    
    self.total_comparisons = len(old_files)
    
    with ThreadPoolExecutor(max_workers=self.core_count) as executor:
      futures = []
      for old_file in old_files:
        old_file_path = os.path.join(self.old_documents_dir, old_file)
        new_file_path = os.path.join(self.new_documents_dir, old_file)
        futures.append(executor.submit(self.compare_pdfs, old_file_path, new_file_path))

      for future in as_completed(futures):
        future.result()

    total_end_time = time.time()
    total_elapsed_time = total_end_time - total_start_time

    print(f"Total time taken for comparing all documents: {total_elapsed_time:.2f} seconds")
    print(f"Average time taken per file: {total_elapsed_time/self.total_comparisons:.2f} seconds")

if __name__ == "__main__":
  comparer = PDFComparer(config)
  comparer.run_comparison()
