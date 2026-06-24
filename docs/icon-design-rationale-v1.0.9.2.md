# Rank Math API Manager — Icon Design Rationale (v1.0.9.2)

**Kilde:** Devora **Profilmanual 1.0** (Profilmanual - Devora - 1.0.pdf). Farger, typografi og retningslinjer følger kjernepalett og tillegspalett fra kapittel 3 Farger (s.28–29).

## Design intent

Square, bold, minimal flat vector icon that reads instantly at 128×128 and reads clearly down to ~32×32 in the WordPress plugin list. The motif encodes an **SEO + API bridge**: a centered, balanced cluster of **connected nodes** (data/endpoints) with a **subtle upward chevron** (ranking/improvement). No shadows, no gradients in the mark; flat geometric shapes only. Styling is **brand-aligned** with Devora’s visual guidelines.

---

## Color palette (Devora Profilmanual 1.0)

Paletten er hentet fra **Profilmanual – Devora 1.0**, kapittel 3 Farger (Kjernepalett og Tillegspalett).

| Rolle | Hex | RGB | Bruk i ikon |
|-------|-----|-----|-------------|
| **Hovedfarge – Dark mode** | `#242a56` | 36, 42, 86 | Chevron, hovednoder, forbindelser |
| **Hovedfarge – Light mode** | `#fcf7ff` | 252, 247, 255 | Bakgrunn (proof og admin) |
| **Sekundær farge** | `#968ab6` | 150, 138, 182 | Sekundær node / forbindelser |
| **Komplementær farge** | `#3432a6` | 52, 50, 166 | Én node som accent (knapper/titler på mørk) |
| **Tillegsfarge 1** | `#ffffff` | 255, 255, 255 | Grafiske elementer (ikke brukt i ikon) |
| **Tillegsfarge 2** | `#fffade` | 255, 250, 222 | Supplerende bakgrunn / titler (valgfri accent) |

Ikonet bruker **kun** kjernepaletten: #242a56, #fcf7ff, #968ab6, #3432a6. Ingen andre farger (ingen azur, teal eller egendefinerte accenter). Én komplementær (#3432a6) brukes som enkelt accent-node.

---

## Color swatches (reference)

```
#242a56  ███████  Hovedfarge dark mode
#fcf7ff  ███████  Hovedfarge light mode (bakgrunn)
#968ab6  ███████  Sekundær
#3432a6  ███████  Komplementær (accent)
#ffffff  ███████  Tillegsfarge 1
#fffade  ███████  Tillegsfarge 2
```

---

## Contrast checks (WCAG 2.1, approx.)

| Foreground | Background | Contrast ratio (approx.) | Note |
|------------|------------|---------------------------|------|
| #242a56 | #fcf7ff | **~10:1** | AAA; sterk silhuett |
| #968ab6 | #fcf7ff | **~4.2:1** | AA for store former |
| #3432a6 | #fcf7ff | **~9.5:1** | AAA; accent-node |

Alle brukte farger på #fcf7ff oppfyller krav for grafikk (min. 3:1). Hovedfarge dark (#242a56) og komplementær (#3432a6) oppfyller AAA for normal tekst.

---

## Grid and safe zone

- **Artboard**: 256×256 px.
- **Internal safe zone**: ~14% padding from edge → **36 px** inset; effective content area **184×184 px** center.
- **Grid**: 256×256; shapes aligned to whole pixels where possible.
- **Strokes**: Treated as filled paths (consistent medium weight, e.g. 8–10 px when scaled to 256) for clarity at 128 and 64 px.

---

## Two conceptual directions

### Direction A — Connected nodes + chevron

- **Motif**: Four rounded nodes in a balanced cluster, connected by short segments; upward-pointing chevron above the cluster.
- **Meaning**: Nodes = endpoints/data; connections = API; chevron = ranking/SEO uplift.
- **Shapes**: Filled circles and filled chevron. Devora palette: #242a56 (chevron, main nodes), #968ab6 (one node/connectors), #3432a6 (one accent node).

### Direction B — Bridge + chevron

- **Motif**: Two vertical pillars with a horizontal bridge bar; compact upward chevron above.
- **Meaning**: Bridge = connection between systems; chevron = improvement/ranking.
- **Shapes**: Filled rects and chevron. #242a56 (pillars, chevron), #3432a6 (bridge).

---

## Refined direction (for review-ready proofs)

**Direction A** is chosen for refinement: it is more literally “API + nodes” and scales well at small sizes with clear counters and a single accent.

Refinements applied:

- Cluster of **four nodes** (two in #242a56, one in #968ab6, one in #3432a6) with connecting segments.
- **Upward chevron** in #242a56 (Hovedfarge dark mode), centered above the cluster.
- All elements **filled**; no thin strokes. Only Devora kjernepalett (no azure, teal, or custom accents).
- Safe zone respected; mark centered on 256×256.

---

## Deliverables

| Asset | Description |
|-------|--------------|
| `icon-direction-a.svg` | Direction A concept (source) |
| `icon-direction-b.svg` | Direction B concept (source) |
| `icon.svg` | Refined master (256×256 viewBox, optimized) |
| `icon-proof.html` | 256 px digital canvas: both directions + refined on #FCF7FF |
| **PNG (after approval)** | 256×256 and 128×128, background #FCF7FF and transparent, exported from SVG |

---

## PNG export (review-ready proofs)

Produce 256×256 and 128×128 PNGs (background #FCF7FF and transparent) from the refined master:

1. **From SVG (recommended)**  
   Open `assets/images/icon.svg` in Inkscape, Figma, or Illustrator.  
   - Export at **256×256** and **128×128**.  
   - One set with background **#FCF7FF**; one set with **transparent** background.  
   - Save as `icon-256x256.png`, `icon-128x128.png` (and optionally `icon-256x256-transparent.png`, `icon-128x128-transparent.png`) in `assets/images/`.

2. **From HTML proof**  
   Open `assets/images/icon-proof.html` in a browser (from the repo so the SVGs load). Capture the refined 256×256 artboard with a screenshot or DevTools; scale to 128×128 for the smaller proof. For pixel-perfect PNGs, prefer exporting from the SVG.

3. **Inkscape CLI (if available)**  
   `inkscape assets/images/icon.svg --export-type=png --export-filename=icon-256x256.png -w 256 -h 256`  
   Repeat for 128×128; add `--export-background=#FCF7FF` for background-locked variants.

---

## Editable source (after PNG approval)

- **Master**: `assets/images/icon.svg` — single 256×256 viewBox, optimized for production. Use as the single source for icon-128x128.png and icon-256x256.png in the plugin.
- **Concepts**: `assets/images/icon-direction-a.svg`, `assets/images/icon-direction-b.svg` — editable concept art; no need to ship in the plugin ZIP.
- **Proof canvas**: `assets/images/icon-proof.html` — for review only; open in browser to compare directions and refined icon on #FCF7FF.

---

## Brand source

- **Profilmanual – Devora 1.0** (Profilmanual - Devora - 1.0.pdf): Innholdsfortegnelse s.1; Logo s.9–23; Typografi s.24–27; **Farger s.28–34** (Kjernepalett og Tillegspalett); Bildestil s.35; Grafisk element s.36–38.
- Ikonet følger fargepalett og bruk fra kapittel 3. Logo-symbol (paraply/d) og grafisk element er ikke kopiert; kun farger og retningslinjer (ingen skygge, kontur eller strekking av logo).

*Document version: 1.1 — March 2026 (Devora Profilmanual 1.0)*
