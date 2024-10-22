class TextExtractor:

  def __init__(self):
    pass
  
  def extract_text(self, page):
    """Extract text from a PDF page with their positions, line by line."""
    words = page.get_text("words") # Extract words with positions
    lines = {}
    for word in words:
      line_key = word[1] # Use bottom y-coordinate as a unique key for the line
      if line_key not in lines:
        lines[line_key] = []
      lines[line_key].append({
        "text": word[4],
        "bbox": word[:4] # Bounding box of the word
      })
    return lines