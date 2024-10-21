import os
import time
import shutil
from io import BytesIO
import pymupdf
from PIL import Image
from text_extractor import extract_text
from text_comparer import compare_text
from image_utils import render_page_to_image, overlay_differences

class PDFComparer:
  def __init__(self, old_documents_dir, new_documents_dir, output_dir, quality=2.0, font_size = 8):
    self.old_documents_dir = old_documents_dir
    self.new_documents_dir = new_documents_dir
    self.output_dir = output_dir
    self.zoom_x = quality
    self.zoom_y = quality
    self.font_size = font_size * quality

    # Ensure output directory exists
    os.makedirs(self.output_dir, exist_ok=True)
    self.clear_output_folder()

  def clear_output_folder(self):
    """Clear the output folder at the start of the script."""
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

  def compare_pdfs(self, old_file_path, new_file_path):
    old_doc = pymupdf.open(old_file_path)
    new_doc = pymupdf.open(new_file_path)
    output_doc = pymupdf.open() #Create a new PDF for the output

    differences_found = False

    for page_num in range(min(len(old_doc), len(new_doc))):
      old_page = old_doc.load_page(page_num)
      new_page = new_doc.load_page(page_num)

      # Render pages to images using the compatible method
      old_image = render_page_to_image(old_page, self.zoom_x, self.zoom_y)
      new_image = render_page_to_image(new_page, self.zoom_x, self.zoom_y)

      # Convert rendered images directly to PIL format
      old_image_pil = Image.frombytes("RGB", [old_image.width, old_image.height], old_image.samples)
      new_image_pil = Image.frombytes("RGB", [new_image.width, new_image.height], new_image.samples)

      # Overlay only the differences from the new image onto the old image
      combined_image = overlay_differences(old_image_pil, new_image_pil, tint_color=(170, 51, 106), opacity=0.5)

      # Extract and compare text from both pages
      old_text_with_positions = extract_text(old_page)
      new_text_with_positions = extract_text(new_page)
      word_diffs = compare_text(old_text_with_positions, new_text_with_positions)

      if combined_image is not None or word_diffs:
        differences_found = True

        # Convert combined image to bytes in a supported format (PNG)
        if combined_image is not None:
          img_byte_array = BytesIO()
          combined_image.save(img_byte_array, format='PNG')
          img_byte_array.seek(0)

        # Insert the combined image into the PDF page
        page = output_doc.new_page(width=old_image.width, height=old_image.height)
        if combined_image is not None:
          page.insert_image(page.rect, stream=img_byte_array, keep_proportion=True)

        # Add word-level text differences to the output PDF, aligning words with their bounding box positions
        if word_diffs:
          current_x_position = {} # Track current x position for each line to avoid overlap
          for word, bbox, change_type in word_diffs:
            if word.startswith('+ '):
              text_color = (0,0.8,0) # Green for added words
              word_text = word[2:]
            elif word.startswith('- '):
              text_color = (0.8,0,0) # Red for removed words
              word_text = word[2:]

            # Calculate the width of the word text using the font object
            text_width = pymupdf.get_text_length(word_text, fontsize=self.font_size)

            # Determine the position for the text box based on the bounding box coordinates and margin offset
            text_pos_x = float(bbox[0]) * self.zoom_x
            text_pos_y = float(bbox[1]) * self.zoom_y

            # Adjust text_pos_x to avoid overlap
            if text_pos_y in current_x_position:
              last_x_position = current_x_position[text_pos_y]
              if last_x_position + pymupdf.get_text_length(" ", fontsize=self.font_size) > text_pos_x:
                # Insert ">" symbol to indicate overlap
                arrow_text = " >"
                arrow_width = pymupdf.get_text_length(arrow_text, fontsize=self.font_size)
                arrow_rect = pymupdf.Rect(last_x_position, text_pos_y - self.font_size, last_x_position + arrow_width, text_pos_y + self.font_size)
                page.insert_textbox(arrow_rect, arrow_text, fontsize=self.font_size, color=(0,0,0))
                # Adjust text position
                text_pos_x = last_x_position + arrow_width + pymupdf.get_text_length(" ", fontsize=self.font_size)

            text_rect = pymupdf.Rect(text_pos_x, text_pos_y - self.font_size, text_pos_x + text_width, text_pos_y + (self.font_size * 2))

            if not text_rect.is_infinite and not text_rect.is_empty:
              page.insert_textbox(text_rect, word_text, fontsize=self.font_size, color=text_color)
              current_x_position[text_pos_y] = text_pos_x + text_width

        # Explicitly delete large objects to free memory
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
      print(f"No PDF files found in the old documents directory: {self.old_documents_dir}")
      return

    if not new_files:
      print(f"No PDF files found in the new documents directory: {self.new_documents_dir}")
      return

    total_start_time = time.time()

    for index, old_file in enumerate(old_files):
      old_file_path = os.path.join(self.old_documents_dir, old_file)
      new_file_path = os.path.join(self.new_documents_dir, old_file)

      if not os.path.exists(new_file_path):
        print(f"New file corresponding to {old_file} not found in the new documents directory.")
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
        print(f"Differences found for {output_file_path}.")
      else:
        print(f"No differences found for {old_file}.")

      print(f"Time take for {old_file}: {elapsed_time:.2f} seconds\n")

    total_end_time = time.time()
    total_elapsed_time = total_end_time - total_start_time
    print(f"Total time taken to compare {len(old_files) * 2} files: {total_elapsed_time:.2f} seconds")

if __name__ == "__main__":
  OLD_DOCUMENT_DIR = "./Old_Documents"
  NEW_DOCUMENT_DIR = "./New_Documents"
  OUTPUT_DIR = "./Output"

  comparer = PDFComparer(OLD_DOCUMENT_DIR, NEW_DOCUMENT_DIR, OUTPUT_DIR, quality=2.0)
  comparer.run_comparison()