# Report Templates

## ANALYSIS.md

```markdown
# {APP} - Competitive Analysis

> Date: {DATE} | Version: {VERSION} | Method: {METHOD}

## Executive Summary
| Metric | Value |
|--------|-------|
| Onboarding screens | {N} |
| Input methods | {N} |
| Price (annual) | {PRICE} |

## Company Profile
| Attribute | Value |
|-----------|-------|
| Company | {NAME} |
| HQ | {LOCATION} |
| Founded | {YEAR} |

## Target Market
### Segment A ({PCT}%)
- Profile: {PROFILE}
- Motivation: {MOTIVATION}

## Onboarding Flow
| Stage | Screens | Purpose |
|-------|---------|---------|

## Psychology
- Social Proof: {DESC}
- Gamification: {DESC}

## Pricing
| Plan | Price |
|------|-------|
| Monthly | {PRICE} |
| Annual | {PRICE} |

## Design System
```css
--primary: {HEX};
--accent: {HEX};
--radius: {PX};
```

## Navigation
| Tab | Function |
|-----|----------|

## Features
| Feature | Free | Premium |
|---------|------|---------|

## Recommendations
1. {REC}

## Screenshot Index
| File | Content |
|------|---------|
| {app}_01.png | {DESC} |
```

## USER_FLOWS.md

```markdown
# {APP} - User Flows

## Navigation
\`\`\`mermaid
flowchart TD
    TAB1[Tab 1] --> CONTENT1
    TAB2[Tab 2] --> CONTENT2
\`\`\`

## Onboarding
\`\`\`mermaid
flowchart TD
    START([Launch]) --> WELCOME
    WELCOME --> QUESTIONS
    QUESTIONS --> PAYWALL
    PAYWALL --> HOME([Home])
\`\`\`

## Core Feature
\`\`\`mermaid
flowchart TD
    HOME --> ADD[+]
    ADD --> METHOD1
    ADD --> METHOD2
    METHOD1 --> RESULT
    RESULT --> SAVE --> HOME
\`\`\`
```

## REPORT.html

```html
<!DOCTYPE html>
<html>
<head>
<style>
:root{--primary:#1E3A5F;--accent:#4ECDC4;--bg:#F5F7FA}
body{font-family:system-ui;background:var(--bg);margin:0;padding:20px}
.container{max-width:1200px;margin:0 auto}
.card{background:#fff;border-radius:12px;padding:24px;margin:20px 0;box-shadow:0 2px 8px rgba(0,0,0,0.1)}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px}
.gallery img{width:100%;border-radius:8px;border:1px solid #eee}
h1,h2{color:var(--primary)}
h2{border-bottom:2px solid var(--accent);padding-bottom:8px}
table{width:100%;border-collapse:collapse}
th,td{padding:12px;text-align:left;border-bottom:1px solid #eee}
th{background:var(--bg)}
</style>
</head>
<body>
<div class="container">
<h1>{APP} - Competitive Analysis</h1>
<div class="card"><h2>Screenshots</h2>
<div class="gallery">
<img src="../.app-analyzer/screenshots/screen_001_home.png">
<img src="../.app-analyzer/screenshots/screen_002_settings.png">
</div></div>
</div>
</body>
</html>
```
