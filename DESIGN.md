# Design System Strategy: The Academic Exchange

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Scholarly Curator."** 

Moving away from the cluttered, utilitarian look of traditional marketplaces, this system treats student listings like high-end gallery pieces. We achieve this through **Editorial Minimalism**: a philosophy that prioritizes intentional white space, asymmetrical layouts, and high-contrast typography. By utilizing a "layered paper" approach rather than a "boxed grid," the UI feels like a premium digital publication—one that is both authoritative and inviting. We break the template look by allowing elements to overlap slightly and by using a dramatic typography scale that demands attention.

---

## 2. Colors & Surface Philosophy
The palette is rooted in heritage but executed with modern depth. We avoid the "flat" look by utilizing a sophisticated tier of surfaces.

### The "No-Line" Rule
**Strict Mandate:** Designers are prohibited from using 1px solid borders for sectioning or containment. Boundaries must be defined solely through background color shifts. 
*   Place a `surface-container-lowest` card on a `surface-container-low` background to create definition. 
*   Use `surface-dim` for global footers to anchor the page without a hard line.

### Surface Hierarchy & Nesting
Treat the interface as a physical stack of fine stationery:
*   **Base Layer:** `surface` (#f8f9fa) – The canvas.
*   **Section Layer:** `surface-container-low` (#f3f4f5) – Used to group related content blocks.
*   **Elevated Layer:** `surface-container-lowest` (#ffffff) – Used for primary interactive cards or modals to make them "pop" against the grey.

### The "Glass & Gold" Rule
To elevate the UWA Gold (#FFB81C) beyond a flat accent:
*   **Signature Textures:** Use subtle linear gradients for primary CTAs, transitioning from `primary` (#001d59) to `primary_container` (#003087) at a 135-degree angle.
*   **Glassmorphism:** For floating navigation bars or filter overlays, use `surface` with an 80% opacity and a `backdrop-blur-md` (Tailwind) to allow the content colors to bleed through softly.

---

## 3. Typography: Editorial Authority
We pair the structural stability of **Inter** with the geometric character of **Manrope** to create a high-end academic feel.

*   **Display & Headlines (Manrope):** Large, bold, and unapologetic. Use `display-lg` (3.5rem) for hero sections to create an editorial impact. The tight tracking and heavy weight convey confidence.
*   **Titles & Body (Inter):** Highly legible and professional. Use `title-lg` (1.375rem) for listing names to ensure clarity.
*   **Labels (Inter):** Small, all-caps with increased letter spacing (0.05em) to provide a "metadata" look for categories or price tags.

---

## 4. Elevation & Depth
In this system, depth is felt, not seen. We replace harsh shadows with **Tonal Layering**.

*   **The Layering Principle:** Instead of a shadow, place a `surface_container_highest` (#e1e3e4) element behind a `surface_container_lowest` (#ffffff) element. This creates a "soft lift" that feels organic to the screen.
*   **Ambient Shadows:** If a floating state is required (e.g., a dragged listing), use an ultra-diffused shadow: `shadow-[0_20px_50px_rgba(0,29,89,0.08)]`. Note the use of a tinted `primary` color in the shadow rather than pure black.
*   **The "Ghost Border" Fallback:** If accessibility requires a stroke, use `outline_variant` at **15% opacity**. It should be a suggestion of a boundary, not a wall.

---

## 5. Components

### Buttons (The "Soft-Command" Pattern)
*   **Primary:** Background gradient (`primary` to `primary_container`), `rounded-full`, `text-on_primary`. High-end feel with no border.
*   **Secondary:** `surface-container-high` background with `primary` text. Provides a tactile feel without the visual weight.
*   **Tertiary:** Ghost style. No background, `primary` text, with a `secondary` (Gold) underline on hover.

### Listing Cards
*   **Strict Rule:** No dividers. Use `spacing-6` (1.5rem) of internal padding to let content breathe.
*   **Structure:** Image (top), followed by a `surface_container_lowest` content area. The price tag should use the `secondary_container` (Gold) as a subtle background chip with `on_secondary_container` text.

### Input Fields
*   **Style:** Minimalist. No bottom line, no full box. Use a `surface_container_high` background with a `rounded-md` (0.75rem) corner.
*   **Focus State:** The background shifts to `surface_container_highest` with a 2px `secondary` (Gold) left-accent bar.

### Navigation Overlays
*   Use Glassmorphism (`bg-surface/80 backdrop-blur-xl`) for any element that sits atop the main content, ensuring the "Swap-Meet" energy is always visible beneath the surface.

---

## 6. Do’s and Don’ts

### Do:
*   **Use Asymmetry:** Place a large `display-md` headline off-center to create a modern, curated look.
*   **Embrace White Space:** Use `spacing-16` or `spacing-20` between major sections to define the "High-End" experience.
*   **Layer Surfaces:** Always ask, "Can I define this area with a subtle color shift instead of a line?"

### Don’t:
*   **Don't use 100% Black:** Use `on_surface` (#191c1d) for text to maintain a premium, ink-on-paper feel.
*   **Don't use Standard Shadows:** Avoid Tailwind’s default `shadow-md` or `shadow-lg`. They are too "heavy" for this scholarly aesthetic.
*   **Don't Grid-Lock:** Avoid perfectly symmetrical 3-column grids. Try a 2/3 and 1/3 split to create visual interest in listing views.
*   **Don't use Dividers:** Never use `<hr>` or `border-b`. Use a `spacing-8` gap or a background color transition to separate content.