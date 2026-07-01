---
name: presentation
description: "Skill to generate professional presentations with strict CSS layout and the Marp framework."
tools:
  - compile_presentation
  - write_file
  - web_search
  - image_search
  - view_image
---

# Professional Presentation Generation

As an expert in presentation design, your role is to design and compile ultra-professional slide decks using Markdown and the Marp framework. The tool to use to finalize the work is `compile_presentation`.

## 1. Writing Rules (Content)
- **Extreme Concision**: NEVER write full sentences on the slides. Use only short, impactful keywords.
- **MANDATORY Syntactic Parallelism**: Your bullet points and titles must follow a parallel syntactic logic. (Example: If the first bullet point is a verb in the infinitive, all bullet points on the slide must start with a verb in the infinitive. If it's a noun phrase, they all must be).
- **Speaker Notes**: At the end of EACH slide (before the `---` separator), always add an HTML comment like this to write the actual speech (full sentences):
  ```html
  <!-- Speaker Notes -->
  <!-- Write the full text the speaker will read here, with context and details. -->
  ```

## 2. Visual Structure and Navigation
- **Breadcrumb Trail (Plan Reminder)**: Each slide (except for the Title page, the "Agenda/Sommaire" page, and the Conclusion) MUST start with this HTML block to remind the general plan, putting the `active` class on the current chapter:
  ```html
  <div class="plan-bar">
    <span class="active">1. Chapter 1</span> <span class="sep">/</span>
    <span>2. Chapter 2</span> <span class="sep">/</span>
    <span>3. Conclusion</span>
  </div>
  ```
- **Columns Layout**: Favor column structures to space out the content, using pure HTML tags (avoid markdown inside the HTML block to prevent parser bugs):
  ```html
  <div class="columns">
    <div class="col-left">
      <p>Descriptive text</p>
      <ul><li>Bullet point 1</li></ul>
    </div>
    <div class="col-right">
      <img src="..." alt="...">
    </div>
  </div>
  ```
- **Integrated Visuals**: Never use dummy/placeholder images or empty spaces. Always use the `image_search` and `vision` tools to source, analyze, and insert real and relevant images from the web.

## 3. Mandatory CSS Template (V8)
The design must be luxurious, with locked typography, subtle gradients, and pagination (`paginate: true`).
Your Markdown file MUST ALWAYS start with this exact YAML block. It defines a custom theme (`@theme custom`) that overrides all default Marp settings:

```markdown
---
marp: true
theme: custom
size: 16:9
paginate: true
style: |
  /* @theme custom */
  * { box-sizing: border-box; margin: 0; padding: 0; }
  
  /* Global structure aligned top left */
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
  
  /* Title Page */
  section.lead { justify-content: center; align-items: center; text-align: center; padding: 80px; }
  
  /* Page numbering */
  section::after {
    content: attr(data-marpit-pagination);
    position: absolute; bottom: 30px; right: 80px;
    font-size: 16px; color: #64748b; font-weight: 500;
  }

  /* Rigid Typography */
  h1 { font-size: 56px; background: -webkit-linear-gradient(45deg, #38bdf8, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px; font-weight: 700; }
  h2 { color: #38bdf8; font-size: 42px; border-bottom: 2px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-bottom: 30px; font-weight: 500; width: 100%; }
  p, li { font-size: 26px; line-height: 1.5; margin-bottom: 15px; color: #cbd5e1; font-weight: 300; width: 100%; }
  ul { margin-left: 30px; margin-bottom: 20px; width: 100%; }
  strong { color: #a855f7; font-weight: 500; }

  /* Tables */
  table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 22px; }
  th { background-color: rgba(56, 189, 248, 0.15); color: #38bdf8; text-transform: uppercase; padding: 15px; border-bottom: 2px solid #334155; text-align: left; }
  td { padding: 15px; border-bottom: 1px solid rgba(255,255,255,0.05); }
  tr:nth-child(even) { background-color: rgba(255,255,255,0.02); }

  /* Navigation Breadcrumb */
  .plan-bar {
    position: absolute; top: 30px; left: 80px; right: 80px;
    font-size: 16px; color: #475569; font-weight: 500; text-transform: uppercase; letter-spacing: 1.5px;
    border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 15px;
    display: flex; gap: 15px; align-items: center; width: calc(100% - 160px);
  }
  .plan-bar .active { color: #f8fafc; background: rgba(56, 189, 248, 0.15); padding: 4px 12px; border-radius: 20px; border: 1px solid rgba(56, 189, 248, 0.3); }
  .plan-bar .sep { color: #334155; }

  /* Columns and Images */
  .columns { display: flex; flex-direction: row; gap: 40px; width: 100%; align-items: center; }
  .col-left, .col-right { flex: 1; display: flex; flex-direction: column; }
  .col-right img { border-radius: 12px; width: 100%; max-height: 400px; border: 1px solid #334155; object-fit: cover; }
---
```

## 4. Final Compilation
Once you have generated the Markdown text and saved the file locally (by default a logical name with `.md`), you MUST use the `compile_presentation` tool to generate the interactive HTML file. If the user explicitly asks for another format (PDF or PPTX), provide the corresponding value in `output_format`.
