---
name: clipboard
description: "Interactions avec le presse-papier du système (lecture de données copiées ou écriture de texte)."
tools:
  - read_clipboard
  - write_clipboard
---
1. **Lecture** : Utilise `read_clipboard` si l'utilisateur te demande d'analyser ou d'utiliser le contenu qu'il vient de copier (du texte ou du code).
2. **Gestion des images** : Si le presse-papier contient une image, `read_clipboard` la sauvegardera dans un fichier temporaire. Utilise ensuite `view_image` sur ce fichier pour l'analyser.
3. **Écriture** : Utilise `write_clipboard` pour copier du code généré, des commandes ou des résumés directement dans le presse-papier de l'utilisateur pour lui faire gagner du temps.
