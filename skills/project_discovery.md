---
name: project_discovery
description: "Découverte, analyse structurelle d'un codebase, lecture des consignes locales (AGENT.md, README.md) et inspection de l'état Git."
tools:
  - generate_context_map
  - read_file
  - execute_bash
---
1. **Cartographie du projet** : Si tu commences sur un projet ou si on te demande d'analyser son architecture, utilise en premier lieu `generate_context_map` pour en comprendre l'arborescence globale.
2. **Recherche de règles et documentations** : Recherche activement à la racine des fichiers comme `AGENT.md`, `README.md`, `CONTRIBUTING.md` ou la configuration (`package.json`, `pyproject.toml`, etc.). Lis-les avec `read_file` pour assimiler les consignes, conventions de style et technologies requises.
3. **Statut Git** : Utilise `execute_bash` pour exécuter `git status` et `git log -n 5` afin de comprendre l'état de la copie de travail, la branche active et les derniers changements.
4. **Validation avant action** : Assure-toi d'avoir une bonne vision d'ensemble de la structure et des règles locales avant d'effectuer la moindre modification de code.
