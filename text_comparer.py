import difflib

def compare_text(old_text_with_positions, new_text_with_positions):
  """Compare text from two PDF pages and return only added or removed words with positions."""
  old_text = []
  new_text = []

  # Collect all words from the old page
  for line in old_text_with_positions.values():
    for word in line:
      old_text.append(word)

  # Collect all words from the new page
  for line in new_text_with_positions.values():
    for word in line:
      new_text.append(word)

    old_words = [word["text"] for word in old_text]
    new_words = [word["text"] for word in new_text]

    diff = list(difflib.ndiff(old_words, new_words))
    word_diffs = []

    old_index = 0
    new_index = 0
    for word in diff:
      if word.startswith('+ '):
        if new_index < len(new_text):
          word_diffs.append((word, new_text[new_index]["bbox"], "add")) # Use the entire bounding box
        new_index += 1
      elif word.startswith('- '):
        if old_index < len(old_text):
          word_diffs.append((word, old_text[old_index]["bbox"], "remove")) # Use the entire bounding box
        old_index += 1
      else:
        old_index += 1
        new_index += 1

  return word_diffs