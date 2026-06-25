---
name: clipboard
description: "Interactions with the system clipboard (reading copied data or writing text)."
tools:
  - read_clipboard
  - write_clipboard
---
1. **Reading**: Use `read_clipboard` if the user asks you to analyze or use the content they just copied (text or code).
2. **Handling Images**: If the clipboard contains an image, `read_clipboard` will automatically save it to a temporary file. Then use `view_image` on this file path to analyze it.
3. **Writing**: Use `write_clipboard` to copy generated code, commands, or summaries directly to the user's clipboard to save them time.
