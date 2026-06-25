---
name: delegation
description: "Délégation de tâches complexes ou parallèles à des sous-travailleurs, ou sollicitation d'un avis externe (peer review, audit de sécurité)."
tools:
  - spawn_adaptive_worker
---
1. Si tu reçois une requête qui demande plusieurs étapes complexes, de l'exploration de code massive, ou des tâches pouvant être parallélisées, utilise `spawn_adaptive_worker` pour créer des sous-travailleurs.
2. **Revue Externe / Double Regard** : N'hésite pas à utiliser `spawn_adaptive_worker` pour obtenir un avis externe neutre ou une revue de code (peer review) sur ton propre travail ou des choix de conception. Configure le worker avec des directives de persona adaptées (ex: "Agis comme un auditeur de code hyper pointilleux" ou "Recherche les failles logiques de cet algorithme").
3. Formule la sous-requête de manière claire et auto-contenue pour le sous-travailleur.
4. Si la tâche nécessite une rigueur particulière, utilise le paramètre `directives` pour imposer un persona au travailleur (ex: "Agis comme un expert sécurité", "Agis comme un architecte logiciel").
5. Demande toujours au sous-travailleur d'enregistrer son travail dans un fichier, pour ne pas saturer ton propre contexte.
