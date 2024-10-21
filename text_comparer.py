import difflib

def compare_text(old_text_with_positions, new_text_with_positions):
  """Compare text from two PDF pages and return only added or removed words with positions."""
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
      if word.startswith('+ '):
        if new_index < len(new_line):
          word_diffs.append((word, new_line[new_index]["bbox"], "add")) # Use the entire bounding box
        new_index += 1
      elif word.startswith('- '):
        if old_index < len(old_line):
          word_diffs.append((word, old_line[old_index]["bbox"], "remove")) # Use the entire bounding box
        old_index += 1
      else:
        old_index += 1
        new_index += 1

  return word_diffs