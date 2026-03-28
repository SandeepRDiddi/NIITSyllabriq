# NIIT StackRoute — Design Document Template Guide

> **COMPLIANCE RULE**: Every design document produced for NIIT StackRoute MUST follow this template exactly. No divergence in structure, typography, colors, or fixed sections is permitted.

---

## 1. Document Overview

This guide captures the complete specification of the **NIIT_Stackroute_Design Document Template.docx**. It is the single source of truth for all program design documents. When generating a new design document — whether by Claude, a local LLM, or a human author — this guide must be followed to the letter.

---

## 2. Typography Rules (Non-Negotiable)

| Element | Font | Size | Color | Bold |
|---|---|---|---|---|
| Cover course title | Candara | 28pt | `#E97132` (orange) | Yes |
| Major section headings | Candara | 20pt | `#0F4761` (navy) | No |
| Sub-section headings | Candara | 14pt | `#0F4761` (navy) | No |
| Section page label ("Course: …") | Candara | 14pt | `#0F4761` (navy) | Yes |
| Total Duration label | Candara | 12pt | `#000000` (black) | Yes (label only) |
| Body text / paragraphs | Candara | 12pt | `#000000` (black) | No |
| Bullet list items | Candara | 11pt | `#000000` (black) | No |
| Footer text | Candara | 9pt  | `#000000` (black) | No |

**Never substitute Candara with another font.**
**Never use colors not listed above.**

---

## 3. Page Layout

- **Paper size**: A4 (11906 × 16838 DXA)
- **Margins**: 1 inch (1440 DXA) on all sides
- **Content width**: 9026 DXA (~6.27 inches)

---

## 4. Header (All Pages After Cover)

- **NIIT StackRoute logo** anchored to the top-right corner
- A **gray decorative horizontal bar** spans the page width
- Font: Candara, 10pt, black

> The header images are fixed assets from the template — carry them forward unchanged.

---

## 5. Footer (All Pages)

```
© NIIT 2025-26                              [center empty]          Page X of Y
All Information within this document is Intellectual property of NIIT (NIIT Ltd).
No part of this document or the program design or program structure mentioned within
can be shared or used within any organization without the permission of NIIT (NIIT Ltd).
```

- Font: Candara, 9pt, black
- Tab stops: center at 4513 DXA, right-align at 9026 DXA

> The footer text is fixed and must not be altered.

---

## 6. Cover Page (Page 1)

**Required elements — in this exact layout:**

1. **Background image**: Full-page AI robot illustration (`image4.jpg`) — anchored, wraps both sides
2. **StackRoute logo** (`image2.png`) — anchored top-right
3. **Course title** — formatted as:
   ```
   Course: [Program Name]
   ```
   - Font: Candara, 28pt, bold, color `#E97132`

4. Remove the instruction note `[The sections mentioned in the document are indicative…]` when generating real documents.

---

## 7. Document Body — Section Order

Sections **must appear in this exact order**. Do not reorder, skip required sections, or rename headings.

```
Page 2 onwards →
  [Page label: "Course: [Program Name]" — bold, Candara 14pt, #0F4761]
  [Total Duration: X Hours]

  1. Program Introduction          ← REQUIRED
  2. Indicative Design and Content Coverage  ← REQUIRED
  3. Pre-requisites                ← REQUIRED
  4. Key Outcomes                  ← REQUIRED
  5. Detailed Design:              ← REQUIRED
  [Optional sections here, e.g., Case Study Details, Capstone]
  6. Learning Pedagogy             ← REQUIRED — FIXED CONTENT — DO NOT EDIT
  7. About StackRoute              ← REQUIRED — FIXED CONTENT — DO NOT EDIT
```

---

## 8. Section Specifications

### 8.1 Program Introduction
- **Heading**: "Program Introduction"
- **Style**: Heading1, Candara 20pt, `#0F4761`, not bold
- **Content**: 2–3 paragraphs providing a brief overview of the program
- **Body format**: Candara 12pt, black, justified, line spacing 276/auto

---

### 8.2 Indicative Design and Content Coverage
- **Heading**: "Indicative Design and Content Coverage"
- **Style**: Heading1, Candara 20pt, `#0F4761`, not bold
- **Content**: High-level summary of content scope — may be a table, diagram description, or paragraph overview

---

### 8.3 Pre-requisites
- **Heading**: "Pre-requisites"
- **Style**: Heading1, Candara 14pt, `#0F4761`, not bold
- **Content**: Bullet-point list of pre-requisite knowledge/skills
- **Bullet format**: Candara 11pt, black, 160 DXA spacing after, 276/auto line spacing

---

### 8.4 Key Outcomes
- **Heading**: "Key Outcomes"
- **Style**: Heading1, Candara 14pt, `#0F4761`, not bold
- **Fixed intro line** (mandatory, word-for-word):
  > After completing this program, participants will be able to:
- **Content**: Bullet-point list using action verbs (design, build, implement, analyze, evaluate, create, demonstrate, apply…)
- **Bullet format**: Candara 12pt, black

---

### 8.5 Detailed Design:
- **Heading**: "Detailed Design:"  (note the colon — it's part of the heading)
- **Style**: Heading1, Candara 14pt, `#0F4761`, not bold
- **Content**: A **table** is the preferred format. Minimum required columns:

| Column | Required |
|---|---|
| Module Name | ✅ Yes |
| Sub-topics | ✅ Yes |
| Duration (Hours) | ✅ Yes |
| Hands-on | Optional |
| Tools Needed | Optional |

Additional columns/rows may be added. Sub-modules can be nested rows.

---

### 8.6 Learning Pedagogy — ⚠️ FIXED — DO NOT MODIFY

This section has fixed boilerplate content. Copy it exactly:

---
**Learning Pedagogy**

The pedagogic model is focused on experiential learning (In person and remote virtual learning) mode. Some expert mentors shall work with students through the program. Learning is in an environment that combines the convenience of anytime access with the intensity of mentoring.

The model combines the following elements:

1. Instructor-led Live connects: These work on a fixed schedule with recorded versions available to people who missed them.
   - Sessions that provide context.
   - Sessions that demonstrate the usage of tools or technologies
   - Sessions with expert-led demonstrations that provide step-by-step guidance on critical tasks.
   - Sessions that explain best practices.
   - Sessions that explain common pitfalls/issues.
   - Sessions that discuss success stories, case studies and real-world scenarios that provide insight into the practical challenges and solutions.

2. Reference learning material.

---

### 8.7 About StackRoute — ⚠️ FIXED — DO NOT MODIFY

This section has fixed boilerplate content. Copy it exactly:

---
**About StackRoute**

*Established in August 2015, StackRoute® is an NIIT incubated venture. StackRoute provides disruptive IT Learning solutions that produce top-class full-stack developers & tech professionals with deep skills. We have evolved a mechanism of providing immersive experiences backed by mastery learning and individual tutoring that allows us to guarantee outcomes. As a digital transformation partner, StackRoute works with several large, mid & small global IT organizations, Global Incubation Centers (GICs), Global Capability Centers (GCCs) & product engineering teams.*

[StackRoute logo appears inline to the right]

---

## 9. Optional / Extensible Sections

The following sections may be inserted **between "Detailed Design:" and "Learning Pedagogy"** as needed:

- **Case Study Details** — include when the program features case studies
- **Capstone** — include when the program includes a capstone project
- Any other program-specific section (assessments, labs, mentoring schedule, etc.)

All optional sections must use the same heading style: Heading1, Candara 14pt, `#0F4761`, not bold.

---

## 10. Variables / Placeholders

Every new document must fill in the following variables:

| Variable | Description | Location |
|---|---|---|
| `{program_name}` | Full name of the course/program | Cover page title, page label |
| `{total_duration_hours}` | Total hours of the program | Page 2 "Total Duration" field |

---

## 11. Compliance Checklist

Before finalizing any generated document, verify:

- [ ] Font is Candara throughout — no substitutions
- [ ] Cover title: 28pt, bold, orange `#E97132`
- [ ] All section headings use color `#0F4761`
- [ ] "Program Introduction" heading is 20pt
- [ ] All other body headings are 14pt
- [ ] Sections appear in the correct order
- [ ] "Learning Pedagogy" and "About StackRoute" contain exact boilerplate — not paraphrased
- [ ] "Key Outcomes" begins with the exact fixed intro line
- [ ] "Detailed Design:" heading includes the trailing colon
- [ ] Footer contains © NIIT 2025-26, page numbers, and IP notice
- [ ] Header contains NIIT StackRoute logo
- [ ] No section has been skipped or renamed

---

## 12. What Can Be Customized Per Program

| Element | Customizable? |
|---|---|
| Program name | ✅ Yes |
| Total duration | ✅ Yes |
| Program Introduction text | ✅ Yes |
| Indicative Design coverage | ✅ Yes |
| Pre-requisites bullets | ✅ Yes |
| Key Outcomes bullets | ✅ Yes |
| Detailed Design table rows | ✅ Yes |
| Additional optional sections | ✅ Yes |
| Learning Pedagogy content | ❌ No — Fixed |
| About StackRoute content | ❌ No — Fixed |
| Font family | ❌ No — Candara always |
| Colors | ❌ No — Palette locked |
| Header/footer content | ❌ No — Fixed |
| Section order | ❌ No — Fixed order |
| Section heading names | ❌ No — Must match exactly |
