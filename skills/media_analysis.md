---
name: media_analysis
description: "Reading, analyzing, and extracting information from complex technical documents (PDFs, images, diagrams, large log files). Do NOT use this for creative writing, literary critique, or story analysis."
tools:
  - read_pdf
  - ask_document
  - view_image
  - read_file
---
1. **Document Reading**: Use `read_pdf` for PDF files and `read_file` for standard text files.
2. **Large Documents**: For large text files or PDFs, prefer `ask_document` to ask targeted questions instead of loading the entire file into your context window.
3. **Image Analysis (Multimodality)**: Use `view_image` to analyze screenshots, diagrams, architecture schemas, or mockups. Provide a specific prompt to guide the analysis (e.g., "What error is shown in this console?").
