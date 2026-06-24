# Résumé détaillé de la gestion des registres dans `discovery.py`

Ce document décrit en détail le fonctionnement des quatre registres globaux gérés par `discovery.py` :
`available_agents`, `available_tools`, `available_skills` et `available_engines`.

---

## 1. Architecture générale — Résolution des chemins (Path Resolution)

Tous les registres partagent un mécanisme commun de recherche de fichiers via la fonction **`get_resolution_paths(subdir_name)`**. Cette dernière retourne une liste de trois tuples `(directory, package_name)` dans l'ordre suivant :

| Priorité | Source                          | Package name          |
|----------|---------------------------------|-----------------------|
| 1 (basse)    | `Catalyst-CLI/<subdir>`           | `default_<subdir>`      |
| 2 (moyenne)| `~/.catalyst/<subdir>`             | `user_<subdir>`          |
| 3 (haute)  | `.catalyst/<subdir>` (CWD local)   | `local_<subdir>`         |

Le principe est que **les fichiers trouvés plus tard dans la liste écrasent ceux des chemins précédents** en cas de conflit (même nom). Par exemple, un fichier `my_agent.md` placé dans `.catalyst/agents/` remplacera celui qui porterait le même nom dans `~/.catalyst/agents/`, lui-même remplaçant la version par défaut du paquet Catalyst.

Les sous-dossiers concernés sont :
- `tools` → chargement des outils (`.py`)
- `engines` → chargement des moteurs (`.py`)
- `agents` → chargement des agents (`.md` ou `.py`)
- `skills` → chargement des compétences (`.md`)

---

## 2. `available_tools` — Registre des Outils

### Structure
```python
available_tools = {}   # dict[str, callable]  — nom de l'outil → fonction
tools_schema    = []   # list[dict]            # schémas JSON compatibles OpenAI pour le LLM
```

### Mécanisme de chargement (`load_tools()`)

1. **Parcours des répertoires** : pour chaque `(directory, package_name)` retourné par `get_resolution_paths("tools")`…
2. **Filtrage des fichiers** : seuls les fichiers `.py` (sauf `__init__.py`) sont traités.
3. **Chargement dynamique du module** : le fichier est importé via `importlib.util.spec_from_file_location()`, ce qui permet de charger un module à partir d'un chemin arbitraire sans qu'il ne soit installé comme paquet Python.
4. **Extraction des schémas** : le module chargé peut exposer soit :
   - `module.schemas` (liste de schémas), soit
   - `module.schema` (un seul schéma, emballé dans une liste).
5. **Validation du nom de l'outil** : les noms commençant par `delegate_to_` ou `deleguate_to_` sont refusés car ils sont réservés aux outils de délégation générés automatiquement.
6. **Vérification des doublons** : si un outil porte déjà le même nom, une `ValueError` est levée.
7. **Injection de contraintes** : les schémas voient leur champ `parameters.additionalProperties` forcé à `False` pour empêcher le LLM d'envoyer des paramètres non attendus (anti-hallucination).
8. **Enregistrement** : la fonction correspondante (`getattr(module, name)`) est associée au nom dans `available_tools`, et le schéma est ajouté à `tools_schema`.

### Points clés
- Les outils sont des **fonctions Python brutes**, enregistrées par leur nom tel qu'elles sont définies dans les modules.
- Les schémas (JSON-like) sont stockés séparément dans `tools_schema` pour être envoyés au LLM lors de l'appel d'un agent.

---

## 3. `available_engines` — Registre des Moteurs (Engines)

### Structure
```python
available_engines = {}       # dict[str, class]  — nom du moteur → classe Engine
engine_descriptions = {}     # dict[str, str]    — nom du moteur → description textuelle
```

### Mécanisme de chargement (`load_engines()`)

1. **Parcours des répertoires** : idem que pour les outils, via `get_resolution_paths("engines")`.
2. **Filtrage des fichiers** : seuls les `.py` (sauf `__init__.py`) sont traités.
3. **Chargement dynamique du module** : idem que pour les outils.
4. **Extraction de la classe Engine** : le module doit exposer une variable nommée `Engine` qui est une **classe Python**. Si cette classe n'existe pas, le fichier est ignoré silencieusement (sauf exception levée).
5. **Nom du moteur** : extrait de `module.ENGINE_NAME`, ou à défaut du nom du fichier (sans `.py`). Le nom est converti en minuscules pour l'enregistrement.
6. **Description** : extraite de `module.ENGINE_DESCRIPTION` (chaîne vide par défaut).
7. **Enregistrement** : la classe et sa description sont associées au nom (minuscule) dans les deux dictionnaires respectifs.

### Points clés
- Les moteurs ne sont pas instanciés ici ; ce sont des **classes prêtes à être instanciées** plus tard lors du chargement des agents.
- Contrairement aux outils, les erreurs de chargement des moteurs sont **silencieuses** (sauf exception explicite), rendant le chargement tolérant aux fichiers mal formés.

---

## 4. `available_agents` — Registre des Agents

### Structure
```python
available_agents = {}  # dict[str, object]  — nom de l'agent → instance d'Agent (ou sous-classe)
```

### Mécanisme de chargement (`load_agents()`)

Les agents peuvent être définis de **deux manières** : via un fichier Markdown (`.md`) ou via un module Python (`.py`). Le parcourt suit le même schéma de résolution multi-répertoires.

#### 4a. Agents Markdown (`.md`)

1. **Lecture du fichier** avec `parse_agent_markdown(filepath)` qui retourne un dictionnaire contenant les métadonnées et le prompt système.
2. **Parsing du front-matter YAML-like** : si le fichier commence par `---`, le contenu entre les deux délimiteurs est analysé ligne par ligne pour extraire les clés/valeurs :
   - `name` (obligatoire), `description`, `engine`, `tools` (liste ou chaîne), `delegates` (liste ou chaîne), `delegation_instruction`.
   - Le texte après le second `---` devient le `system_prompt`.
   - Les valeurs entre crochets `[a, b, c]` sont automatiquement converties en listes.
3. **Validation du nom** : le nom doit correspondre à l'expression régulière `^[a-zA-Z0-9_]+$` (alphanumérique + underscores uniquement).
4. **Vérification des doublons** : une `ValueError` est levée si un agent porte déjà le même nom.
5. **Normalisation de `delegates`** : s'il est fourni comme chaîne, il est converti en liste à un élément ; `None` devient une liste vide.
6. **Instanciation de l'Agent** : un objet `Agent` temporaire est créé avec les métadonnées parsées.
7. **Liaison au moteur** : le nom du moteur (ex: `"ReAct"`) est recherché dans `available_engines` ; la classe correspondante instancie l'agent (`engine_class(temp_config)`). Si le moteur n'est pas trouvé, une `ValueError` est levée.
8. **Enregistrement** : l'agent instancié est stocké sous son nom dans `available_agents`.

#### 4b. Agents Python (`.py`)

1. **Chargement dynamique du module** : idem que pour les outils et moteurs.
2. **Recherche de classes héritant de `BaseAgent`** : toutes les attributs du module sont parcourus ; ceux qui sont des types, sous-classes de `BaseAgent` (et non `BaseAgent` lui-même), sont instanciés.
3. **Enregistrement** : l'instance est stockée dans `available_agents` via son attribut `.name`.

### Points clés
- La résolution multi-répertoires permet d'**écraser un agent par défaut** avec une version utilisateur ou locale.
- Les agents sont **instantanément liés à leur moteur**, ce qui signifie que le moteur doit avoir été chargé avant l'agent (garanti car `load_engines()` est appelé avant `load_agents()`).

---

## 5. `available_skills` — Registre des Compétences

### Structure
```python
available_skills = {}  # dict[str, Skill]  — nom de la compétence → instance de Skill
```

### Mécanisme de chargement (`load_skills()`)

1. **Parcours des répertoires** : via `get_resolution_paths("skills")`.
2. **Filtrage des fichiers** : seuls les fichiers `.md` sont traités (les `.py` sont ignorés).
3. **Parsing du front-matter** : idem que pour les agents Markdown, utilisant la même fonction `parse_agent_markdown()`.
4. **Nom de la compétence** : extrait du champ `name` ou dérivé du nom du fichier sans extension.
5. **Vérification des doublons** : une `ValueError` est levée si une compétence porte déjà le même nom.
6. **Normalisation de `tools`** : si fourni comme chaîne, converti en liste à un élément ; `None` devient une liste vide.
7. **Instanciation de Skill** : un objet `Skill(name, description, tools, directives)` est créé.
8. **Enregistrement** : l'objet est stocké sous son nom dans `available_skills`.

### Résolution des compétences (`resolve_skills(skill_names)`)

Cette fonction prend une liste de noms de compétences et retourne un tuple `(resolved_tools, combined_directives)` :
- Elle parcourt chaque compétence demandée (en ignorant les noms inexistants).
- Pour **chaque outil** dans `skill.tools`, si l'outil n'a pas encore été vu (`seen_tools`), il est ajouté à la liste plate `resolved_tools`. Les doublons sont donc évités.
- Pour **chaque directive**, elle ajoute un bloc formaté `"## Skill: {name}\n{directives}"` aux parties à concaténer.
- Le résultat final est une liste d'outils sans doublon et un texte de directives combinées par `"\n\n"`.

### Points clés
- Les compétences sont **uniquement Markdown** — pas de chargement Python.
- Elles fonctionnent comme des **abstractions sur les outils** : une compétence regroupe plusieurs outils et fournit des directives contextuelles pour le LLM.
- La résolution est **plate** (flat) : un outil mentionné dans plusieurs compétences n'apparaît qu'une seule fois dans la liste finale.

---

## 6. Outils de délégation générés automatiquement (`generate_delegation_tools()`)

Après le chargement de tous les agents, cette fonction parcourt `available_agents` et crée pour chacun un outil de délégation :

1. **Nom de l'outil** : `delegate_to_{agent_name}` (ex: `delegate_to_web_researcher`).
2. **Fonction générée** (`make_delegate_func`) : utilise une closure avec un paramètre par défaut (`name=agent_name`) pour capturer correctement la valeur de l'agent. La fonction :
   - Incrémente le `nesting_level` (variable contextuelle).
   - Récupère le callback d'étape courant via `current_step_callback`.
   - Appelle `target_agent.run(query, history=[], step_callback=parent_callback)`.
   - Décrémente le `nesting_level` dans un bloc `finally`.
3. **Description** : `"Delegates a complex sub-task to the specialized agent '{name}'. Description: {agent_obj.description}"`, enrichie de la `delegation_instruction` si fournie.
4. **Schéma JSON** : crée un schéma avec un seul paramètre requis `query` (type string, description détaillée demandant une instruction auto-contenue).
5. **Enregistrement** : l'outil et son schéma sont ajoutés respectivement à `available_tools` et `tools_schema`.

Ces outils de délégation sont créés **après tous les chargements**, ce qui garantit que tous les agents cibles existent déjà dans le registre.

---

## 7. Ordre d'exécution au démarrage

Au bas du fichier, l'initialisation se fait dans cet ordre précis :

```python
load_tools()        # 1 → charge available_tools + tools_schema
load_engines()      # 2 → charge available_engines + engine_descriptions
load_skills()       # 3 → charge available_skills
load_agents()       # 4 → charge available_agents (nécessite engines chargés)
generate_delegation_tools()  # 5 → ajoute les outils de délégation à available_tools + tools_schema
```

Cet ordre est crucial car :
- Les agents dépendent des **engines** (pour l'instanciation).
- La génération des outils de délégation dépend que **tous les agents soient chargés**.
- Les outils sont chargés en premier afin qu'ils puissent être référencés par les compétences et les agents.

---

## 8. Variables contextuelles globales

En plus des quatre registres, `discovery.py` définit trois variables contextuelles (`contextvars.ContextVar`) utilisées pour le suivi d'exécution :

| Variable | Valeur par défaut | Usage |
|----------|-------------------|-------|
| `nesting_level` | `0` | Suit la profondeur de délégation (agents imbriqués) |
| `current_step_callback` | `None` | Callback appelé à chaque étape d'exécution d'un agent |
| `active_agent_name` | `"catalyst"` | Nom de l'agent actuellement en cours d'exécution |

Ces variables sont thread-safe et isolées par contexte, permettant un suivi correct même dans des exécutions concurrentes.

---

## 9. Résumé visuel des relations entre registres

```
┌──────────────┐       ┌───────────────┐
│ available_   │       │ available_    │
│ engines      │◄──────│ engines       │
│              │ class │ descriptions  │
└──────▲───────┘       └───────────────┘
       │                 ▲
       │ instance        │
       ▼                 │
┌──────────────┐   .py   │
│ available_   │◄───────┘
│ agents       │  (Engine class)
│              │
│ ┌──────────┐ │
│ │ delegate │ │◄──── generate_delegation_tools()
│ │ _to_*    │ │     creates tools in...
│ └─────▲────┘ │
└───────┼──────┘        ▲
        │               │
        │ references    │ appends to
        ▼               │
┌──────────────┐   .py │
│ available_   │◄──────┘
│ tools        │  (schema)
│              │
└──────▲───────┘
       │ list of names
       │ resolves via
       ▼
┌──────────────┐
│ available_   │ .md
│ skills       │
│              │
│ ┌───────┐    │◄── tools → available_tools
│ │ tools │────┘
│ └───────┘
└──────────────┘
```
---

## 10. Exemple concret : le skill `git_ops`

Le fichier `skills/git_ops.md` définit la compétence **git_ops** dont voici le contenu intégral et l'analyse détaillée :

### Fichier source (`skills/git_ops.md`)
```markdown
---
name: git_ops
description: "Opérations de versionnage Git : staging, diff, log, branches."
tools:
  - execute_bash
---
1. Limite-toi aux opérations Git : `git status`, `git diff`, `git log`, `git add`, `git branch`, `git stash`.
2. Ne jamais exécuter `git push` ou `git commit` sans demande explicite de l'utilisateur.
3. Utilise `git log --oneline -n 20` plutôt que `git log` pour limiter la taille de la sortie.
```

### Analyse du front-matter

| Champ          | Valeur                                                        |
|----------------|---------------------------------------------------------------|
| `name`         | `git_ops`                                                     |
| `description`  | `"Opérations de versionnage Git : staging, diff, log, branches."` |
| `tools`        | `[execute_bash]`                                              |

### Outils associés au skill `git_ops`

Ce skill fait appel à **un seul outil** :

| Outil            | Détail |
|------------------|--------|
| `execute_bash`   | Permet d'exécuter des commandes shell, ici spécifiquement des commandes Git. |

> Lors de la résolution via `resolve_skills(["git_ops"])`, la liste plate des outils résolus sera `[execute_bash]`.

### Directives du skill (à injecter dans le prompt système)

Lorsqu'un agent active ce skill, les directives suivantes sont concaténées au prompt :

```markdown
## Skill: git_ops
1. Limite-toi aux opérations Git : `git status`, `git diff`, `git log`, `git add`, `git branch`, `git stash`.
2. Ne jamais exécuter `git push` ou `git commit` sans demande explicite de l'utilisateur.
3. Utilise `git log --oneline -n 20` plutôt que `git log` pour limiter la taille de la sortie.
```

Ces directives guident le LLM dans son utilisation des outils Git : restriction du périmètre, verrou sur les actions destructrices (`push`, `commit`) sans consentement explicite, et limitation de la verbosité par défaut.
