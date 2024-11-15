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

# Load configuration from config.json
with open('config.json', 'r') as config_file:
  config = json.load(config_file)
  
# Set default core count if not specified by the user
if config["core_count"] is None:
  config["core_count"] = int(os.cpu_count() * 1.5)

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
    self.batch_size = config["batch_size"]
    self.core_count = config["core_count"]

    self.image_utils = ImageUtils(self.quality)
    self.text_comparer = TextComparer()

    # Ensure output directory exists
    os.makedirs(self.output_dir, exist_ok=True)
    self.clear_output_folder()

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

  def add_text_differences(self, page, word_diffs):
    """Add word-level text differences to the PDF page
    :param page: PDF page to annotate.
    :param word_diffs: List of word-level differences with bounding boxes"""
    current_x_position = {} # Track current x position for each line to avoid overlap

    for word, bbox in word_diffs:
      if word.startswith('+ '):
        text_color = (0, 0.8, 0) # Green for added words
        word_text = word[2:]
      elif word.startswith('- '):
        text_color = (0.8, 0, 0) # Red for removed words
        word_text = word[2:]

      # Calculate the width of the word text using the default font
      text_width = pymupdf.get_text_length(word_text, fontsize=self.font_size)

      # Determine the position for the text box based on the bounding box coordinates
      text_pos_x = float(bbox[0]) * self.quality
      text_pos_y = float(bbox[1]) * self.quality

      # Adjust text_pos_x to avoid overlap
      if text_pos_y in current_x_position:
        last_x_position = current_x_position[text_pos_y]
        if last_x_position + pymupdf.get_text_length(" ", fontsize=self.font_size) > text_pos_x:
          # Insert " >" symbol to indicate overlap
          arrow_text = " >"
          arrow_width = pymupdf.get_text_length(arrow_text, fontsize=self.font_size)
          arrow_rect = pymupdf.Rect(last_x_position, text_pos_y - self.font_size, last_x_position + arrow_width, text_pos_y + (self.font_size * 2))
          page.insert_textbox(arrow_rect, arrow_text, fontsize=self.font_size, color=(0,0,0))
          # Adjust text position
          text_pos_x = last_x_position + arrow_width + pymupdf.get_text_length(" ", fontsize=self.font_size)

      text_rect = pymupdf.Rect(text_pos_x, text_pos_y - self.font_size, text_pos_x + text_width, text_pos_y + (self.font_size * 2))

      if not text_rect.is_infinite and not text_rect.is_empty:
        page.insert_textbox(text_rect, word_text, fontsize=self.font_size, color=text_color)
        current_x_position[text_pos_y] = text_pos_x + text_width

  def compare_pdfs(self, old_file_path, new_file_path):
    """
    Compare two PDF files and return a document with differences highlighted
    :param old_file_path: Path to the old PDF file
    :param new_file_path: Path to the new PDF file
    :return: PDF document with differences highlighted"""
    output_file_path = os.path.join(self.output_dir, f"diff_{os.path.basename(old_file_path)}")
    start_time = time.time()
    
    with open_pdf(old_file_path) as old_doc, open_pdf(new_file_path) as new_doc:
      output_doc = pymupdf.open() #Create a new PDF for the output

      differences_found = False

      for page_num in range(min(len(old_doc), len(new_doc))):
        old_page = old_doc.load_page(page_num)
        new_page = new_doc.load_page(page_num)

        # Render pages to images
        old_image_pil, new_image_pil = self.image_utils.render_pages_to_images(old_page, new_page)

        # Overlay differences
        combined_image = self.image_utils.overlay_differences(old_image_pil, new_image_pil, tint_color=(170,51,106))

        # Extract and compare text
        word_diffs = self.text_comparer.extract_and_compare_text(old_page, new_page)

        if combined_image is not None or word_diffs:
          differences_found = True

          # Convert combined image to bytes in a supported format (PNG)
          if combined_image is not None:
            combined_image = combined_image.convert('RGB')
            img_byte_array = BytesIO()
            combined_image.save(img_byte_array, format='JPEG', quality=85)
            img_byte_array.seek(0)

          # Insert the combined image into the PDF page
          page = output_doc.new_page(width=old_image_pil.width, height=old_image_pil.height)
          if combined_image is not None:
            page.insert_image(page.rect, stream=img_byte_array, keep_proportion=True)

          # Add word-level text differences to the output PDF
          if word_diffs:
            self.add_text_differences(page, word_diffs)

          # Explicitly delete large objects to free memory
          if combined_image is not None:
            del combined_image
            del img_byte_array
          del old_image_pil
          del new_image_pil

          gc.collect()

    if differences_found:
      output_doc.save(output_file_path)
    output_doc.close()
    end_time = time.time()
    elapsed_time = end_time - start_time
    return output_file_path, False, elapsed_time

  def compare_batch(self, batch_pairs):
    """Compare a batch of PDF files"""
    batch_results = []
    for old_file_path, new_file_path in batch_pairs:
      if not os.path.exists(new_file_path):
        print(f"New file corresponding to {old_file_path} not found in the new documents directory.")
        continue
      result = self.compare_pdfs(old_file_path, new_file_path)
      batch_results.append(result)
    return batch_results
  
  def run_comparison(self):
    """Run the comparison for all PDFs in the specified directories"""
    old_files = self.get_pdf_files(self.old_documents_dir)
    new_files = self.get_pdf_files(self.new_documents_dir)

    if not old_files:
      print(f"No PDF files found in the old documents directory: {self.old_documents_dir}")

    if not new_files:
      print(f"No PDF files found in the new documents directory: {self.new_documents_dir}")

    total_start_time = time.time()

    def batch_files(files, batch_size):
      """Helper function to batch files into groups"""
      for i in range(0, len(files), batch_size):
        yield files[i:i + batch_size]
    
    with ThreadPoolExecutor(max_workers=self.core_count) as executor:
      futures = []
      for batch in batch_files(old_files, self.batch_size):
        batch_pairs = [(os.path.join(self.old_documents_dir, file), os.path.join(self.new_documents_dir, file)) for file in batch]
        futures.append(executor.submit(self.compare_batch, batch_pairs))

      for future in as_completed(futures):
        batch_results = future.result()
        for output_file_path, differences_found, elapsed_time in batch_results:
          if differences_found:
            print(f"Differences found: {output_file_path}")
          else:
            print(f"No differences found for {output_file_path}")
          print(f"Time taken for {output_file_path}: {((elapsed_time/self.core_count)*self.batch_size):.2f} seconds\n")

    total_end_time = time.time()
    total_elapsed_time = total_end_time - total_start_time

    print(f"Total time taken for comparing all documents: {total_elapsed_time:.2f} seconds")

if __name__ == "__main__":
  comparer = PDFComparer(config)
  comparer.run_comparison()