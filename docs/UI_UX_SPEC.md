# ResearchPilot AI — UI/UX Design Specification

**Version:** 1.1 (Revised)
**Status:** Architecture Phase — Approved for Phase 1
**Last Revised:** 2026-09-11

---

## 1. Design Philosophy

ResearchPilot AI is a **professional AI research workspace**, not a chatbot wrapper. Every design decision should reinforce:

- **Information density with clarity** — researchers want to see the content, not the chrome
- **Grounded intelligence** — the UI clearly communicates what is AI-generated vs. paper-sourced
- **Calm professionalism** — no gaming aesthetics, excessive gradients, or animation noise
- **Structured workflow** — the UI guides the user through a clear research process

The closest design analogues are: Notion, Linear, Perplexity AI (minus the search engine aspects), and Arc Browser's Reader.

---

## 2. Design System

### 2.1 Color Palette

**Base Philosophy:** A slate-dark neutral base with a controlled accent. This reads as professional, academic, and trustworthy.

```css
/* Design Tokens — implemented in tailwind.config.ts and globals.css */

/* Background */
--color-bg-base:        #0A0C10   /* Page background — near-black slate */
--color-bg-surface:     #111318   /* Primary card/panel surface */
--color-bg-elevated:    #1A1D24   /* Elevated surfaces (popovers, modals) */
--color-bg-subtle:      #1E2028   /* Subtle differentiation (sidebar, headers) */

/* Borders */
--color-border-subtle:  #22262F   /* Subtle dividers */
--color-border-default: #2D3141   /* Standard borders */
--color-border-strong:  #3D4255   /* Emphasized borders */

/* Primary Accent — Deep Indigo/Violet */
--color-accent-primary:     #6366F1   /* Indigo-500: CTAs, active states, links */
--color-accent-primary-dim: #4F52C4   /* Hover states */
--color-accent-primary-bg:  #1E1F3A   /* Accent background tints */
--color-accent-glow:        rgba(99, 102, 241, 0.12)  /* Subtle accent glow */

/* Semantic Accent — Research/Insight context */
--color-accent-secondary:   #10B981   /* Emerald-500: success, insights, ready state */
--color-accent-warning:     #F59E0B   /* Amber-500: processing/caution states */
--color-accent-error:       #EF4444   /* Red-500: error states */

/* Text */
--color-text-primary:   #F0F2F7   /* Primary text */
--color-text-secondary: #8B90A0   /* Secondary/muted text */
--color-text-tertiary:  #555C70   /* Tertiary/disabled text */
--color-text-accent:    #818CF8   /* Accent text (Indigo-400) */
```

### 2.2 Typography

```css
/* Font: Inter (Google Fonts) — import in globals.css */

--font-sans: 'Inter', system-ui, -apple-system, sans-serif;

/* Type Scale */
--text-xs:   0.75rem   / 1rem       /* 12px/16px — labels, captions */
--text-sm:   0.875rem  / 1.25rem    /* 14px/20px — secondary text */
--text-base: 1rem      / 1.5rem     /* 16px/24px — body text */
--text-lg:   1.125rem  / 1.75rem    /* 18px/28px — panel headings */
--text-xl:   1.25rem   / 1.75rem    /* 20px/28px — section headings */
--text-2xl:  1.5rem    / 2rem       /* 24px/32px — page headings */
--text-3xl:  1.875rem  / 2.25rem    /* 30px/36px — hero / workspace title */

/* Font Weights */
--font-normal:   400
--font-medium:   500
--font-semibold: 600
--font-bold:     700

/* Letter Spacing */
--tracking-tight:   -0.02em    /* For large headings */
--tracking-normal:   0em
--tracking-wide:     0.05em    /* For LABELS/TAGS in uppercase */
```

### 2.3 Spacing System

Tailwind's default spacing scale extended with project-specific tokens:

```
4px  = 1 unit  (tight internal padding)
8px  = 2 units (element padding)
12px = 3 units (compact card padding)
16px = 4 units (default card padding)
20px = 5 units (comfortable section gap)
24px = 6 units (section padding)
32px = 8 units (large section gap)
48px = 12 units (panel separation)
```

### 2.4 Layout Grid

```
App Layout: Sidebar (240px fixed) + Main Content (flex-grow)
Content Max Width: 1280px
Main Content Padding: 24px horizontal, 24px vertical
Content Area Inner Max Width: 900px (for readability in long text)
```

### 2.5 Elevation / Surface Hierarchy

```
Level 0: bg-base      — page background
Level 1: bg-surface   — primary panels, cards
Level 2: bg-elevated  — dropdowns, modals, popovers
Level 3: bg-subtle    — sidebar, secondary panels
```

### 2.6 Corner Radius

```
--radius-sm:   4px    /* Tags, badges */
--radius-md:   6px    /* Buttons, inputs, small cards */
--radius-lg:   8px    /* Standard cards, panels */
--radius-xl:   12px   /* Large modals, upload zone */
--radius-full: 9999px /* Pills */
```

### 2.7 Shadows

```css
/* Subtle card lift */
--shadow-card: 0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2);

/* Elevated component */
--shadow-elevated: 0 4px 12px rgba(0,0,0,0.4), 0 2px 4px rgba(0,0,0,0.2);

/* Modal/dialog */
--shadow-modal: 0 20px 60px rgba(0,0,0,0.6);

/* Accent glow (subtle, on active states) */
--shadow-accent: 0 0 0 3px rgba(99,102,241,0.2);
```

---

## 3. Component Specifications

### 3.1 Sidebar

```
Width:          240px fixed
Background:     bg-subtle (#1E2028)
Right border:   1px solid bg-border-subtle
Padding:        16px vertical, 12px horizontal

Structure:
  ├── Logo area (ResearchPilot + icon)     — top, 56px height
  ├── Navigation section                   — flex column, gap-1
  │   ├── Workspace         [active/hover]
  │   ├── Research Papers   [active in MVP]
  │   └── Settings          [disabled in MVP, shown greyed]
  └── Version / about info                 — bottom, text-xs
```

**Nav item states:**
- Default: text-secondary, no background
- Hover: text-primary, bg-accent-primary-bg subtle
- Active: text-accent, bg-accent-primary-bg, left border 2px accent

### 3.2 Upload Zone

```
Style:          Bordered dashed rectangle
Border:         2px dashed color-border-default, radius-xl
Background:     bg-surface
Hover:          border-accent-primary, bg-accent-primary-bg (subtle transition)
Dragging:       border-accent-primary solid, bg-accent-primary-bg stronger
Height:         200px (not full-screen)
Content:        Upload icon (Lucide FileUp), headline, subtext, browse button
```

### 3.3 Processing Status Component

```
Container:      Card (bg-surface, border, radius-lg, padding-6)
Stages:         Vertical list of pipeline stages with icons
Stage states:
  - Pending:    grey dot + grey text
  - Active:     indigo spinner + indigo text (animated)
  - Complete:   green checkmark + white text
  - Failed:     red X + red text + error message
```

**Stage Labels (user-readable):**
1. Validating file
2. Extracting text
3. Processing content
4. Generating embeddings
5. Building knowledge index

### 3.4 Paper Meta Card

```
Style:          Compact info card at top of workspace
Content:
  ├── File icon + filename (bold)
  ├── Page count badge
  ├── Chunk count badge
  └── Ready status badge (green)
Right side:     "Upload new paper" button (text/ghost style)
```

**Tab navigation (Summary | Paper Insights | Assistant):**
- Tab style: Underline variant (not boxed tabs)
- Active tab: Text-primary, 2px underline in accent color
- Inactive tab: Text-secondary, no underline
- Spacing: gap-6 between tabs
- Labels: "Summary" | "Paper Insights" | "Research Assistant"

> **Important:** The tab is labeled "Paper Insights" — not "Insights" or "Research Trends". This distinction is product-critical.

### 3.6 Research Assistant Message Bubbles

**User message:**
- Right-aligned, max-width 75%
- Background: bg-accent-primary-bg, border: border-default
- Text: text-primary

**Assistant message:**
- Left-aligned, max-width 100%
- No background bubble — clean text on surface
- Answer text: text-primary
- Source references: separate section below answer, visually demarcated

**Source References Section:**
```
Header:    "Sources" label (text-xs, text-tertiary, uppercase tracking-wide)
Items:     List of source chips:
           [document icon] [page/chunk ref] [short excerpt]
Style:     bg-subtle, radius-sm, text-xs
```

### 3.7 Summary Dimension Card

```
Style:     Card (bg-surface, border, radius-lg, padding-4)
Structure:
  ├── Dimension icon + label (text-sm, text-secondary, uppercase)
  ├── Divider
  └── Content text (text-base, text-primary)
Empty:     "Not identified in this paper." (text-tertiary, italic)
```

### 3.8 Insight Card

```
Similar to SummaryDimensionCard but with:
- Color-coded left border per insight type
- Bulleted list rendering for multi-value insights (Findings, Limitations)
```

### 3.9 Buttons

```
Primary:   bg-accent-primary, text-white, radius-md, hover:bg-accent-primary-dim
           font-medium, px-4 py-2
Secondary: bg-transparent, border border-default, text-secondary
           hover: text-primary, border-strong
Ghost:     No bg, no border, text-secondary, hover: text-primary, bg-subtle
Danger:    bg-error/10, text-error, border border-error/30
Disabled:  opacity-40, cursor-not-allowed
```

### 3.10 Inputs / Textarea

```
Background:   bg-surface
Border:       border-default, radius-md
Focus:        border-accent-primary, shadow-accent
Text:         text-primary
Placeholder:  text-tertiary
Font:         text-base
```

### 3.11 Badges / Tags

```
Variants:
  Default:   bg-subtle, text-secondary, radius-sm, text-xs, px-2 py-0.5
  Success:   bg-emerald/10, text-emerald, border border-emerald/20
  Warning:   bg-amber/10, text-amber, border border-amber/20
  Error:     bg-red/10, text-red, border border-red/20
  Info:      bg-indigo/10, text-indigo, border border-indigo/20
```

---

## 4. Application States

### 4.1 Empty Workspace

```
Layout: Centered content, max-w-xl, vertical stack with spacing
Content:
  ├── ResearchPilot logo/wordmark (top-left of centered card)
  ├── H1: "Your AI Research Workspace"
  ├── Subheading: 2-line product description
  ├── Upload Zone (prominent, centered)
  ├── Supported formats note (text-xs, text-tertiary)
  └── How it works: 3-step visual (Upload → Analyze → Ask)
```

### 4.2 Processing State

```
Layout: Centered card, max-w-md
Header: Filename being processed
Content: ProcessingStatus component (vertical stage list)
Footer: Cannot interact with other panels during processing
```

### 4.3 Research Workspace (Active)

```
Layout: Full-width workspace (no centering)
Top:    PaperMetaCard (full-width)
Below:  Tab bar (Summary | Insights | Assistant)
Body:   Tab content area (flex-grow, scrollable)
```

**Summary Tab:**
- 2-column grid on desktop (lg:grid-cols-2)
- Each SummaryDimensionCard in grid
- Overview card spans full width at top

**Insights Tab:**
- Single column, vertical stack of InsightCards

**Assistant Tab:**
- 2-panel layout: messages (left/top, flex-grow) + input (bottom fixed)
- Input: Textarea + Send button
- Suggested queries shown when message list is empty

### 4.4 Error State

```
Centered card with:
  ├── Error icon (Lucide AlertCircle, red)
  ├── Error headline (non-technical)
  ├── Error description
  └── Primary action button ("Try again" or "Upload new paper")
```

---

## 5. Loading & Skeleton States

- All async operations show skeleton loaders (not spinners) for content areas
- Summary tab: 9 skeleton cards during generation
- Insights tab: 7 skeleton cards during generation
- Assistant: Typing indicator (3-dot animation) while generating answer

---

## 6. Responsive Behavior

| Breakpoint | Behavior |
|---|---|
| < 768px (mobile) | Sidebar hidden (hamburger); single column layout |
| 768–1024px (tablet) | Sidebar collapsed to icons only; content adapts |
| > 1024px (desktop) | Full sidebar + multi-column content — primary target |

Desktop is the primary target for MVP. Mobile is a consideration but not the primary demo scenario.

---

## 7. Micro-interactions

- Upload zone: Subtle scale transform (scale-[1.01]) on drag hover
- Button hover: 150ms ease transition on background
- Tab switch: 150ms fade between tab content panels
- Message appear: Subtle slide-up (translateY 4px → 0) + fade-in
- Stage complete: Checkmark icon appears with a quick scale animation
- Loading states: Smooth pulse animation on skeleton elements

These are intentional and purposeful. No decorative animations.

---

## 8. Empty States

Each functional panel has a thoughtful empty state:

| Panel | Empty State Content |
|---|---|
| Summary (no paper) | "Upload a paper to generate a structured summary" |
| Insights (no paper) | "Upload a paper to extract research insights" |
| Assistant (no messages) | Suggested query chips + brief explanation |
| Summary (generating) | Skeleton cards with "Analyzing paper..." message |

---

## 9. Accessibility

- All interactive elements: keyboard navigable
- Focus rings: visible, using accent color outline
- Color contrast: WCAG AA minimum for all text/background combinations
- ARIA labels on icon-only buttons
- Screen reader announcements for processing stage changes
- Form labels properly associated with inputs

---

## 10. Icons

Exclusively use **Lucide React** icons. Icon sizes:
- Sidebar nav: 18px
- Inline text: 14–16px
- Large decorative: 24–32px

No mixing of icon libraries.

---

*This document is the authoritative design reference. All frontend implementation must conform to the tokens, components, and patterns defined here.*
