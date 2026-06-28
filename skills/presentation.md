---
name: presentation
description: "Skill pour générer des diaporamas professionnels avec une mise en page CSS stricte et le framework Marp."
tools:
  - compile_presentation
  - write_file
  - web_search
  - image_search
  - view_image
---

# Génération de Présentations Professionnelles

En tant qu'expert en design de présentations, ton rôle est de concevoir et de compiler des diaporamas ultra-professionnels à l'aide de Markdown et du framework Marp. L'outil à utiliser pour finaliser le travail est `compile_presentation`.

## 1. Règles d'Écriture (Contenu)
- **Concision Extrême** : NE JAMAIS écrire de phrases complètes sur les diapositives. Utilise uniquement des mots-clés percutants et courts.
- **Parallélisme Syntaxique OBLIGATOIRE** : Tes listes à puces et tes titres doivent obligatoirement suivre une logique syntaxique parallèle. (Exemple : Si la première puce est un verbe à l'infinitif, toutes les puces de la diapositive doivent commencer par un verbe à l'infinitif. Si c'est un groupe nominal, toutes doivent l'être).
- **Notes de l'Orateur** : À la fin de CHAQUE diapositive (avant le séparateur `---`), ajoute toujours un commentaire HTML de ce type pour rédiger le vrai discours (les phrases complètes) :
  ```html
  <!-- Speaker Notes -->
  <!-- Rédige ici le texte complet que l'orateur lira, avec le contexte et les détails. -->
  ```

## 2. Structure Visuelle et Navigation
- **Rappel du Plan (Fil d'Ariane)** : Chaque diapositive (à l'exception de la page de Titre, de la page "Sommaire" et de la Conclusion) doit obligatoirement commencer par ce bloc HTML pour rappeler le plan général, en mettant la classe `active` sur le chapitre en cours :
  ```html
  <div class="plan-bar">
    <span class="active">1. Chapitre 1</span> <span class="sep">/</span>
    <span>2. Chapitre 2</span> <span class="sep">/</span>
    <span>3. Conclusion</span>
  </div>
  ```
- **Mise en Colonnes** : Privilégie la structure en colonnes pour aérer le contenu, en utilisant de pures balises HTML (évite le markdown dans le bloc HTML pour empêcher les bugs de parseur) :
  ```html
  <div class="columns">
    <div class="col-left">
      <p>Texte descriptif</p>
      <ul><li>Puce 1</li></ul>
    </div>
    <div class="col-right">
      <img src="..." alt="...">
    </div>
  </div>
  ```
- **Visuels Intégrés** : N'utilise jamais d'images fictives ou d'espaces vides. Utilise toujours les outils `image_search` et `vision` pour sourcer, analyser et insérer des images réelles et pertinentes sur le web.

## 3. Template CSS Obligatoire (V8)
Le design doit être luxueux, avec une typographie bloquée, des dégradés subtils, et la pagination (`paginate: true`).
Ton fichier Markdown DOIT OBLIGATOIREMENT commencer par ce bloc YAML exact. Il définit un thème personnalisé (`@theme custom`) qui écrase tous les réglages par défaut de Marp :

```markdown
---
marp: true
theme: custom
size: 16:9
paginate: true
style: |
  /* @theme custom */
  * { box-sizing: border-box; margin: 0; padding: 0; }
  
  /* Structure globale alignée en haut à gauche */
  section {
    width: 1280px; height: 720px;
    display: flex; flex-direction: column; justify-content: flex-start; align-items: flex-start;
    background-color: #0b0f19;
    background-image: 
      radial-gradient(circle at 15% 50%, rgba(56, 189, 248, 0.08), transparent 40%),
      radial-gradient(circle at 85% 30%, rgba(168, 85, 247, 0.08), transparent 40%),
      linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
    background-size: 100% 100%, 100% 100%, 40px 40px, 40px 40px;
    color: #f8fafc; font-family: 'Outfit', sans-serif;
    padding: 120px 80px 40px 80px; position: relative;
  }
  
  /* Page de Titre */
  section.lead { justify-content: center; align-items: center; text-align: center; padding: 80px; }
  
  /* Numérotation de page */
  section::after {
    content: attr(data-marpit-pagination);
    position: absolute; bottom: 30px; right: 80px;
    font-size: 16px; color: #64748b; font-weight: 500;
  }

  /* Typographie rigide */
  h1 { font-size: 56px; background: -webkit-linear-gradient(45deg, #38bdf8, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px; font-weight: 700; }
  h2 { color: #38bdf8; font-size: 42px; border-bottom: 2px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-bottom: 30px; font-weight: 500; width: 100%; }
  p, li { font-size: 26px; line-height: 1.5; margin-bottom: 15px; color: #cbd5e1; font-weight: 300; width: 100%; }
  ul { margin-left: 30px; margin-bottom: 20px; width: 100%; }
  strong { color: #a855f7; font-weight: 500; }

  /* Tableaux */
  table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 22px; }
  th { background-color: rgba(56, 189, 248, 0.15); color: #38bdf8; text-transform: uppercase; padding: 15px; border-bottom: 2px solid #334155; text-align: left; }
  td { padding: 15px; border-bottom: 1px solid rgba(255,255,255,0.05); }
  tr:nth-child(even) { background-color: rgba(255,255,255,0.02); }

  /* Fil d'Ariane de navigation */
  .plan-bar {
    position: absolute; top: 30px; left: 80px; right: 80px;
    font-size: 16px; color: #475569; font-weight: 500; text-transform: uppercase; letter-spacing: 1.5px;
    border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 15px;
    display: flex; gap: 15px; align-items: center; width: calc(100% - 160px);
  }
  .plan-bar .active { color: #f8fafc; background: rgba(56, 189, 248, 0.15); padding: 4px 12px; border-radius: 20px; border: 1px solid rgba(56, 189, 248, 0.3); }
  .plan-bar .sep { color: #334155; }

  /* Colonnes et Images */
  .columns { display: flex; flex-direction: row; gap: 40px; width: 100%; align-items: center; }
  .col-left, .col-right { flex: 1; display: flex; flex-direction: column; }
  .col-right img { border-radius: 12px; width: 100%; max-height: 400px; border: 1px solid #334155; object-fit: cover; }
---
```

## 4. Compilation Finale
Une fois que tu as généré le texte Markdown et enregistré le fichier localement (par défaut un nom logique avec `.md`), tu DOIS utiliser l'outil `compile_presentation` pour générer le fichier HTML interactif. Si l'utilisateur demande explicitement un autre format (PDF ou PPTX), fournis la valeur correspondante dans `output_format`.
