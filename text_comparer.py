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

import difflib
from text_extractor import TextExtractor

class TextComparer:

  def __init__(self):
    self.text_extractor = TextExtractor()
  
  def compare_text(self, old_text_with_positions, new_text_with_positions):
    """Compare text from two PDF pages and return only added or removed words with positions."""
    old_text = self.collect_text_with_positions(old_text_with_positions)
    new_text = self.collect_text_with_positions(new_text_with_positions)

    old_words = [word["text"] for word in old_text]
    new_words = [word["text"] for word in new_text]

    diff = list(difflib.ndiff(old_words, new_words))
    word_diffs = []

    old_index = 0
    new_index = 0
    for word in diff:
      if word.startswith("+ "):
        if new_index < len(new_words):
          word_diffs.append((word, new_text[new_index]["bbox"]))
        new_index += 1
      elif word.startswith("- "):
        if old_index < len(old_words):
          word_diffs.append((word, old_text[old_index]["bbox"]))
        old_index += 1
      else:
        old_index += 1
        new_index += 1

    return word_diffs

  def collect_text_with_positions(self, text_with_positions):
    """Collect all words with positions from the given text with positions"""
    text_list = [word for line in text_with_positions.values() for word in line]
    return text_list
  
  def extract_and_compare_text(self, old_page, new_page):
    """Extract and compare text from PDF pages."""
    old_text_with_positions = self.text_extractor.extract_text(old_page)
    new_text_with_positions = self.text_extractor.extract_text(new_page)
    word_diffs = self.compare_text(old_text_with_positions, new_text_with_positions)
    return word_diffs
