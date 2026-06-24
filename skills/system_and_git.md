---
name: system_and_git
description: "Exécution de commandes terminal (compilation, diagnostics, tests) et opérations de versionnage Git (status, diff, staging)."
tools:
  - execute_bash
---
1. **Usage général du terminal** : Utilise `execute_bash` pour exécuter des scripts, compiler du code, lancer des diagnostics ou exécuter les tests du projet (essentiel après chaque modification de code pour valider la non-régression).
2. **Opérations Git informatives** : Tu as la liberté de lancer des commandes de lecture comme `git status`, `git diff`, `git log`, `git stash` ou `git branch` pour comprendre le contexte du dépôt.
3. **Contrôle Git strict** : Ne lance jamais de commandes d'écriture altérant le dépôt distant (`git push`) ou créant des commits (`git commit`) sans une consigne explicite et directe de l'utilisateur.
4. **Optimisation des sorties** : Utilise des arguments limitatifs (ex: `git log --oneline -n 20`) ou redirige les sorties trop verbeuses pour éviter d'inonder ton contexte.
