---
name: Lumen Beauty
description: A daylight beauty counter with a collapsing toolbar and cosmetic color in place of product photos.
colors:
  primary: "#e2186a"
  primary-press: "#c11259"
  primary-ink: "#fff7fb"
  ink: "#241433"
  ink-soft: "#4e3d63"
  ground: "#f4f0fa"
  surface: "#ffffff"
  line: "#efe6f6"
  quiet-hover: "#e7dff5"
  choice-selected: "#ffd6e6"
  selection: "#ffc2d8"
  disabled: "#eadfe8"
  error: "#9d123c"
  error-bg: "#ffd9e6"
  ok: "#145c45"
  ok-bg: "#d5f6ea"
  field-skincare: "#dff8f0"
  field-makeup: "#ffe3ef"
  field-service: "#efe6ff"
  edge-rose: "#ff7aa8"
  edge-peach: "#ffb088"
  edge-butter: "#ffe08a"
  edge-mint: "#7ddec0"
  edge-sky: "#8ec8ff"
  edge-lilac: "#c9b0ff"
typography:
  display:
    fontFamily: "Figtree, Segoe UI, sans-serif"
    fontSize: "clamp(2.5rem, 5.4vw, 4.25rem)"
    fontWeight: 700
    lineHeight: 0.96
    letterSpacing: "-0.04em"
  headline:
    fontFamily: "Figtree, Segoe UI, sans-serif"
    fontSize: "clamp(1.6rem, 2.4vw, 2.1rem)"
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: "-0.03em"
  title:
    fontFamily: "Figtree, Segoe UI, sans-serif"
    fontSize: "1.15rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Figtree, Segoe UI, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Figtree, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.2
rounded:
  none: "0"
  pill: "999px"
spacing:
  header-offset: "14px"
  scroll-threshold: "8px"
  row: "0.95rem"
  section: "1.15rem"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0.55rem 1rem"
  button-primary-hover:
    backgroundColor: "{colors.primary-press}"
    textColor: "{colors.primary-ink}"
    rounded: "{rounded.pill}"
  button-primary-active:
    backgroundColor: "{colors.primary-press}"
    textColor: "{colors.primary-ink}"
    rounded: "{rounded.pill}"
  button-quiet:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0.55rem 1rem"
  button-quiet-hover:
    backgroundColor: "{colors.quiet-hover}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
  button-disabled:
    backgroundColor: "{colors.disabled}"
    textColor: "{colors.ink-soft}"
    rounded: "{rounded.pill}"
    padding: "0.55rem 1rem"
  input:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "0.55rem 0.75rem"
    height: "2.75rem"
  input-focus:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "0.7rem 0.7rem 0.85rem"
  nav-bar:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
  choice:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "0.4rem 0.85rem"
    height: "2.75rem"
  choice-selected:
    backgroundColor: "{colors.choice-selected}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
---

# Design System: Lumen Beauty

## Overview

**Creative North Star: "The Daylight Counter"**

Lumen Beauty is a local shop the visitor buys from, not a campaign they read. The room is a cool lilac. The counter is white. Cosmetic color does the job product photography would do: each item is a flat swatch, and each department sits on its own field. The toolbar is the one piece of chrome. It starts as a wide capsule and, after a short scroll, eases into a compact pill so the products stay easy to reach.

Density stays comfortable. Purchase actions are filled pills. Everything else is a change of tone, not a line or a shadow. Copy, prices, and the path from shelf to checkout are product truth. A visual change does not rewrite them.

**Key Characteristics:**

- One face, Figtree, self-hosted, with Segoe UI as the fallback.
- One action color, used on the next thing the shopper does.
- Product color is flat and specific to the item or the department.
- The toolbar is a capsule that collapses on scroll, on desktop.
- Surfaces separate by tone. Shadows appear only on what is floating.
- Motion is short, ease-out for arrivals and presses, ease-in-out for the bar morph.

## Colors

The palette is a lilac room, plum text, and a rose action, with a six-color cosmetic spectrum for products.

### Primary

- **Counter Rose** (`{colors.primary}`): The filled action. Add to cart, checkout, place order, create account, and text links.
- **Pressed Rose** (`{colors.primary-press}`): Hover and the darker moment under a press.
- **Petal Ink** (`{colors.primary-ink}`): Text on a rose fill.

### Secondary

- **Cosmetic spectrum** (`{colors.edge-rose}` through `{colors.edge-lilac}`): The strip under the toolbar, in this order: rose, peach, butter, mint, sky, lilac. The same hues supply product swatches. A new product takes the nearest cosmetic hue that is not already its neighbor's.
- **Department fields**: Skincare is `{colors.field-skincare}`, makeup is `{colors.field-makeup}`, services are `{colors.field-service}`. A new department gets one field, not a gradient.

### Neutral

- **Plum Ink** (`{colors.ink}`): Headings, prices, labels, and running text.
- **Soft Plum** (`{colors.ink-soft}`): Supporting sentences. It is a tint of the ink, not a gray.
- **Lilac Room** (`{colors.ground}`): Page background, quiet buttons, inputs, and rows inside a white panel.
- **Counter White** (`{colors.surface}`): Toolbar, product cards, checkout panel, toast.
- **Hairline Lilac** (`{colors.line}`): The toolbar border, and only once the bar has collapsed.
- **Alert Berry** and **Alert Wash** (`{colors.error}`, `{colors.error-bg}`): Out of stock and error notices.
- **Leaf** and **Leaf Wash** (`{colors.ok}`, `{colors.ok-bg}`): Success notices.

**The One Action Rule.** Rose is the next step. It is not a decoration on headings, section fields, or swatches.

**The Swatch Rule.** Each product has one flat color. Departments have one field. Nothing fades from one into the other.

## Typography

**Display Font:** Figtree (with Segoe UI, then sans-serif)
**Body Font:** Figtree (same stack)

**Character:** One geometric sans, set tight on headlines and at a normal reading size in the body. There is no second face and no monospace.

### Hierarchy

- **Display** (700, `clamp(2.5rem, 5.4vw, 4.25rem)`, line-height 0.96, tracking -0.04em): The page title. One per page.
- **Headline** (700, `clamp(1.6rem, 2.4vw, 2.1rem)`, line-height 1.05, tracking -0.03em): Department and panel headings.
- **Title** (700, 1.15rem, tracking -0.02em): Product names and cart line names.
- **Body** (400, 1.0625rem, line-height 1.5): Descriptions and form copy. Supporting lines use Soft Plum. Prices use Plum Ink at weight 700 with tabular figures.
- **Label** (600, 1rem): Buttons, the wordmark (1.2rem, tracking -0.03em), and form labels.

**The One Face Rule.** Do not add a serif, a script, or a monospace label. Figtree files live with the static assets and load from the font stylesheet.

## Layout

The shop column is `min(1120px, calc(100% - 2.5rem))`, centered. Department bands run the full viewport width and bring their content back into that same column. Checkout and account panels are narrower (42rem and 32rem) and centered in the column.

The toolbar sticks 14px below the top of the viewport. At scroll position 0 it is as wide as the column. After 8px of scroll, on viewports wider than 760px, it shrinks to the measured width of its contents and stays centered. Below 760px the bar stays the width of the screen minus a 1rem inset, and the links wrap onto a second row under the wordmark and the action.

Product cards use an auto-filling grid with a minimum of 220px. Services are two columns, stacking to one on small screens. More space sits above a heading than below it. Section bands are about 1.15rem apart.

**The Purchase Path Rule.** Shop, cart, and the account action stay visible in the toolbar. Do not hide them behind a menu on desktop. On small screens they remain on the bar, not in a drawer.

## Elevation & Depth

Depth is a step in tone: lilac room, then white counter, then a ground-colored row inside a panel. Cards, inputs, and panels have no shadow and no outline.

### Shadow Vocabulary

- **Floating bar** (`box-shadow: 0 10px 28px rgba(36, 20, 51, 0.14)`): The toolbar after it has collapsed. Gone at the top of the page.
- **Toast** (`box-shadow: 0 16px 36px rgba(36, 20, 51, 0.16)`): The only other shadow. The toast is the one element that floats over the page.

**The Flat Rest Rule.** If it is not floating over other content, it does not have a shadow.

## Shapes

Actions are fully round pills (`{rounded.pill}`). Cards, inputs, choice rows, and panels are square (`{rounded.none}`). The toolbar is a capsule: the same pill radius, with the cosmetic strip clipped to the bottom edge. Do not introduce a soft 8–16px radius.

The color strip is six equal flat segments, 0.42rem tall. It is part of the toolbar, not a separate rule under the page.

## Components

### Buttons

- **Shape:** Fully round (`{rounded.pill}`).
- **Primary:** Counter Rose fill, Petal Ink text, padding 0.55rem 1rem, weight 600. On a product card the button is the full width of the card.
- **Hover / Focus:** Hover darkens to Pressed Rose, and only for a fine pointer. Focus is a 2px Counter Rose outline, 3px outside the control. Press scales to 0.97 in 160ms with the ease-out curve, and does not change layout.
- **Quiet:** Lilac Room fill and Plum Ink text. Used for Sign out. A text-only remove control is Counter Rose on a transparent fill.
- **Disabled:** Disabled wash (`{colors.disabled}`) and Soft Plum text. No press scale.

### Cards / Containers

- **Corner Style:** Square.
- **Background:** Counter White on a department field. Cart rows and checkout lines are Lilac Room inside a white panel.
- **Shadow Strategy:** None.
- **Border:** None.
- **Internal Padding:** 0.7rem on a product card. The swatch is a square (16:9 on service cards) in that product's color. The placeholder word in the swatch stays in the markup and is not shown.

### Inputs / Fields

- **Style:** Square, no border, Lilac Room fill, 2.75rem tall.
- **Focus:** Fill turns Counter White. The caret is Counter Rose. The outline is the shared focus ring.
- **Choice rows:** Lilac Room at rest, petal wash (`{colors.choice-selected}`) when selected. The radio uses the accent color.
- **Error / Disabled:** Errors use Alert Wash and Alert Berry. Disabled controls use the disabled button treatment.

### Navigation

Wordmark on the left, Shop, Cart, and Sign in or Account in the middle, one action on the right. The current page is Counter Rose at weight 700. Other links are Plum Ink at weight 500 and turn rose on hover for a fine pointer.

The bar's collapsed width is measured from the row's contents. Do not hard-code it. Transitions stay off until that measurement is applied, so the bar does not animate on first paint. A hash in the URL starts the page in the collapsed state so a deep link does not flash the wide bar. Below 760px there is no width animation.

### Notices

An error or success notice fades down into place (8px, 220ms, ease-out). The added-to-cart toast sits at the bottom right, enters from 12px below, and leaves back the same way in 180ms. It does not block the toolbar.

## Do's and Don'ts

### Do:

- **Do** keep rose for the next purchase or account action, and use the cosmetic spectrum for products.
- **Do** give a new catalog item its own flat swatch, and a new department one field color.
- **Do** keep the toolbar's collapse measured, desktop-only, and shadow-only on small screens.
- **Do** use ease-out (`cubic-bezier(0.23, 1, 0.32, 1)`) for presses and arrivals, and ease-in-out (`cubic-bezier(0.77, 0, 0.175, 1)`) for the bar morph.
- **Do** leave content visible when reduced motion is on. Drop the travel, keep the color and the state.
- **Do** gate hover motion behind a fine pointer.

### Don't:

- **Don't** change product names, prices, summaries, or checkout fields as part of a visual change.
- **Don't** add a second typeface, a gradient, a hairline between sections, or a shadow on a resting card.
- **Don't** hide Shop or Cart, or replace the toolbar with a different navigation model.
- **Don't** animate the bar on first paint, or set its collapsed width by hand.
- **Don't** bring back the warm paper and terracotta look. That was the previous storefront, not this one.
