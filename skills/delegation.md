---
name: delegation
description: "Délégation de tâches complexes ou parallèles à des sous-travailleurs adaptatifs."
tools:
  - delegate_to_adaptive_worker
---
1. Si tu reçois une requête qui demande plusieurs étapes complexes, de l'exploration de code massive, ou des tâches pouvant être parallélisées, utilise `delegate_to_adaptive_worker` pour créer des sous-travailleurs.
2. Formule la sous-requête de manière claire et auto-contenue pour le sous-travailleur.
3. Si la tâche nécessite une rigueur particulière, utilise le paramètre `directives` pour imposer un persona au travailleur (ex: "Agis comme un expert sécurité", "Agis comme un architecte logiciel").
4. Demande toujours au sous-travailleur d'enregistrer son travail dans un fichier, pour ne pas saturer ton propre contexte.
