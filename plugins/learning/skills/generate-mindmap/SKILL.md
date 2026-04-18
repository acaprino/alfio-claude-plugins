---
name: generate-mindmap
description: >
  "Brainstorm and generate a Buzan-style structured mindmap JSON outline from any content. Use this skill whenever the user asks to create a mind map, mappa mentale, concept map, or visual summary. The skill prioritizes COGNITIVE EFFECTIVENESS over structural efficiency: it uses single keywords, strong visual associations (emojis), organic radiant thinking, and cross-linking to maximize memory retention and idea generation.".
  TRIGGER WHEN: the user asks to create a mind map, mappa mentale, concept map, or visual summary -- typically to learn, brainstorm, or structure knowledge around a topic.
  DO NOT TRIGGER WHEN: the user wants a traditional outline, flowchart, or diagram (use Mermaid directly) rather than a radiant Buzan-style mind map.
---

# Generate Mindmap (Buzan Method)

Analyze content and produce a structured mindmap JSON outline. This skill focuses on the intellectual work: extracting core themes, building organic hierarchy, assigning visual attributes, and finding non-linear associations. The output is a renderer-agnostic JSON structure.

## Philosophy: Effectiveness > Efficiency

Do not force symmetrical or perfectly balanced branches. Human thought is organic. Prioritize **cognitive impact**: use highly evocative single words, vivid emojis, and let branches grow naturally based on the richness of the associations.

## Parameters

The user can specify these parameters. If not specified, use **normal** complexity.

### Complexity

| Level         | L2 branches | Max depth | Description                                |
| ------------- | ----------- | --------- | ------------------------------------------ |
| **essential** | 3-5         | 2         | Core concepts only, high-impact synthesis. |
| **normal**    | 5-7         | 4         | Balanced organic exploration (default).    |
| **detailed**  | 7-9         | 6         | Deep, comprehensive associative dive.      |

*Note: Node counts per branch are NOT fixed. Let them flow organically. Some L2 branches may have 10 children, others only 1.*

## Workflow

### Step 1: Analyze content

Identify the core subject, main radiating themes, and hidden connections between different concepts.

### Step 2: Build outline (Radiant Thinking)

1. **Identify the Central Nucleus:** 1-2 words maximum. Create a vivid `central_image_prompt` describing a visual representation of this core.
2. **Extract Main Branches (L2):** The primary categories radiating from the center.
3. **Extract Sub-branches (L3+):** Apply the **Rule of One**: use a SINGLE powerful keyword per node (absolute max 2 words if strictly necessary). Strip all articles, prepositions, and filler words.
4. **Assign Emoji:** Every single node (L2, L3+) MUST have an emoji placed *before* the keyword to act as a visual anchor.
5. **Assign Colors:** Assign a unique hex color to each L2 branch. All children of that branch conceptually inherit this color.
6. **Identify Cross-Links:** Find 1 to 4 non-linear connections between different branches (e.g., a node in Branch 1 that heavily relates to a node in Branch 3).

### Step 3: Output

Write the mindmap in the requested format. Default is **JSON**. Save to a file (e.g., `/tmp/mindmap-outline.json`).

#### JSON format (default)

```json
{
  "root": "🎯 Brainstorming",
  "central_image_prompt": "A glowing human brain with colorful lightning bolts radiating outward",
  "branches":[
    {
      "id": "b1",
      "text": "🎨 Creativity",
      "color": "#ff6b6b",
      "children":[
        { "id": "b1_1", "text": "💡 Ideas" },
        { "id": "b1_2", "text": "🔗 Connections" }
      ]
    },
    {
      "id": "b2",
      "text": "⚙️ Process",
      "color": "#4ecdc4",
      "children":[
        { "id": "b2_1", "text": "⏳ Time" }
      ]
    }
  ],
  "cross_links":[
    { "from": "b1_2", "to": "b2_1", "label": "accelerates" }
  ]
}
```

#### Markdown format

If markdown is requested, produce a nested list. Omit colors and cross-links, but strictly maintain the single-keyword rule and emojis.

## Content Principles (Buzan Rules)

- **The Rule of One:** One node = ONE keyword. Never a phrase, never a sentence. Nouns and strong action verbs only.
- **Visual Memory:** Emojis are not decorative; they are cognitive anchors. Match the emoji to the meaning, not just the word.
- **Organic Growth:** Allow asymmetry. If a concept triggers a deep chain of associations, let it go deep (up to max depth).
- **Opposites/Tensions:** Use contrasting symbols (e.g., ☀️/🌧️, ✅/❌).

## Semantic Emoji Code (Fallback)

Use specific emojis when applicable, otherwise use domain-specific ones:

| Function         | Emoji | Function         | Emoji |
| :--------------- | :---- | :--------------- | :---- |
| Central Concept  | 🎯    | Concrete Example | 💡    |
| Definition/Core  | 📌    | Metric/Data      | 📊    |
| Process/Action   | ⚙️    | Person/Role      | 👤    |
| Advantage/Pro    | ✅    | Time/Phase       | ⏳    |
| Limit/Con        | ❌    | Warning/Risk     | ⚠️    |

## Color Palette (L2 branches)

Use these high-contrast, brain-friendly colors for L2 branches:

| #  | Color    | Hex     |
| -- | -------- | ------- |
| 1  | Coral    | #ff6b6b |
| 2  | Teal     | #4ecdc4 |
| 3  | Lime     | #95e77e |
| 4  | Mint     | #a8e6cf |
| 5  | Peach    | #ffd3b6 |
| 6  | Lavender | #d4a5f5 |
| 7  | Yellow   | #f7dc6f |
| 8  | Sky      | #85c1e9 |

## JSON Schema Requirements

- **root** (string): Central theme (1-2 words + emoji).
- **central_image_prompt** (string): A short prompt describing a visual illustration of the root.
- **branches** (array): List of branch objects.
- **Branch object:** Must include `id` (unique string, e.g., "node_1"), `text` (emoji + single keyword), and `color` (L2 only).
- **cross_links** (array): Objects containing `from` (id), `to` (id), and optional `label` (1 word).
