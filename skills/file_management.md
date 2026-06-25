---
name: file_management
description: "Reading, writing, and modifying files on the local filesystem."
tools:
  - read_file
  - write_file
  - append_file
  - patch_file
---
1. Use `read_file` to read files, never use `cat` in the terminal.
2. For large documents (>200 lines), write incrementally using `append_file` to avoid response truncation.
3. Always verify if a file exists before writing to it to avoid accidentally overwriting existing content.
4. **File-First Output**: Do not output large files or drafts directly in your chat responses. Write them directly to files on disk and give the user the file path.
