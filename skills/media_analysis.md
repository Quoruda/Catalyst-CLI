---
name: media_analysis
description: "Lecture, analyse et extraction d'informations depuis des documents complexes (PDF, images, schémas, gros documents)."
tools:
  - read_pdf
  - ask_document
  - view_image
  - read_file
---
1. **Lecture de documents** : Utilise `read_pdf` pour les fichiers PDF et `read_file` pour les fichiers textuels standards.
2. **Documents volumineux** : Pour les gros documents textuels ou PDF, privilégie `ask_document` pour poser des questions ciblées au lieu de charger tout le fichier dans ton contexte.
3. **Analyse d'images (Multimodalité)** : Utilise `view_image` pour analyser des captures d'écran, diagrammes, schémas d'architecture ou maquettes. Donne un prompt précis pour orienter l'analyse (ex: "Quelle erreur s'affiche dans cette console ?").
