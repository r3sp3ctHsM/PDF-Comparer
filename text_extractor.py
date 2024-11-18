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
