---
name: delegation
description: "Capacité à déléguer des tâches complexes ou isolées à des sous-travailleurs dynamiques pour exécuter des actions en parallèle ou segmenter les problèmes."
tools:
  - delegate_to_adaptive_worker
---
1. Si la tâche qui t'est confiée est très complexe (ex: "code une app web complète", "fais des recherches et crée un repo git"), ne tente pas de tout faire toi-même dans la même session.
2. Utilise `delegate_to_adaptive_worker` pour créer des sous-travailleurs (sub-workers) qui s'occuperont d'une partie spécifique du problème.
3. Sois très précis dans le paramètre `query` : donne tout le contexte nécessaire au sous-travailleur et précise où il doit sauvegarder son travail.
4. N'hésite pas à utiliser le paramètre `directives` pour forcer le sous-travailleur à adopter un rôle très précis (ex: "Agis comme un développeur senior très strict").
