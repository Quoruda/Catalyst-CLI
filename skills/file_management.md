---
name: file_management
description: "Lecture, écriture et modification de fichiers sur le système local."
tools:
  - read_file
  - write_file
  - append_file
  - patch_file
---
1. Utilise `read_file` pour lire des fichiers, jamais `cat` via le terminal.
2. Pour les documents volumineux (>200 lignes), écris de manière incrémentale avec `append_file` pour éviter les troncatures JSON.
3. Vérifie toujours qu'un fichier existe avant d'écrire dessus pour ne pas écraser du contenu existant par erreur.
