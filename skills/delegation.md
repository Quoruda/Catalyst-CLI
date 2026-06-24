---
name: delegation
description: "Capacité à paralléliser ou isoler des tâches complexes en déléguant à des sous-travailleurs adaptatifs."
tools:
  - delegate_to_adaptive_worker
---
1. Si tu reçois une tâche extrêmement complexe ou qui nécessite de mélanger plusieurs domaines d'expertise différents, utilise `delegate_to_adaptive_worker`.
2. Utilise cet outil pour créer un contexte propre (isoler la mémoire et les outils) pour une sous-tâche spécifique.
3. Remplis le champ `query` avec une instruction très détaillée et complète. Le sous-travailleur n'a pas accès à ton historique, tu dois tout lui expliquer.
4. Utilise le champ `directives` si tu souhaites imposer une posture stricte au sous-travailleur (ex: "Agis comme un expert Git très strict").
5. Ne délègue pas les tâches simples (comme lire un fichier ou chercher sur le web) que tu peux faire toi-même en utilisant d'autres skills.
