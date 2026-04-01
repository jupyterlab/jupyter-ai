# Hero Icon Animation

Animated hero banner for the Jupyter AI landing page. Included from `index.md` via:

```
{raw} html
:file: _templates/hero-icon.html
```

To swap to the simple (static) hero, change the include to `_templates/simple-hero-icon.html`.

## Layout

- Left column: programming language icons scrolling UP
- Center: Jupyter logo (static)
- Right column: AI provider icons scrolling DOWN
- SVG "pipes" connecting each column to the Jupyter logo

## How the Animation Works

Each column is a tall vertical strip of icons inside a short container with
`overflow:hidden`, so only 3 icons are visible at a time. A CSS animation
shifts the strip by one icon height (72px) per "tick".

The animation has two phases per tick (see `@keyframes`):
- 0%–60%: hold still (icon is displayed)
- 80%–100%: slide to the next icon (smooth transition)

After each tick completes (`animationiteration` event), JavaScript updates the
CSS variable `--offset` to set the new resting position for the next tick.

## Why Are the Icons Duplicated?

The strip contains duplicate copies of the icon set to create a seamless
infinite loop. When the animation reaches the end of one copy, the JS resets
`--offset` to the same position in another copy. Since the copies are identical,
this jump is invisible to the user.

### Left column (ticks UP): 2 copies needed

The strip scrolls upward, so new icons enter from the BOTTOM. Browsers
aggressively pre-render content below the visible area (optimized for
downward scrolling), so the next icon is already painted when it enters.
When the strip reaches the end of copy 1, JS jumps back to copy 1's start
(the duplicate below ensures continuity during the last tick).

### Right column (ticks DOWN): 3 copies needed

The strip scrolls downward, so new icons enter from the TOP. Browsers do
NOT pre-render content above the visible area as aggressively. With only
2 copies, the icon entering from above hasn't been composited yet, causing
a visible rendering glitch (brief flash/delay).

With 3 copies, the strip starts positioned in the MIDDLE copy. This means
there's always a full pre-rendered copy above the visible window. The
browser paints these during initial layout, so they're ready when they
scroll into view. When the strip scrolls up into the first copy, JS jumps
back to the same position in the middle copy (seamless).

## Icon Sources

- **Language icons**: [Devicon](https://devicon.dev/) (MIT license) via jsDelivr CDN.
  Using `-plain` variants for monochrome SVGs (except Rust which only has `-original`).

- **AI provider icons**: [Lobe Icons](https://github.com/lobehub/lobe-icons) (MIT license) via unpkg CDN.

- **Kiro icon**: downloaded from kiro.dev, stored locally at `_static/kiro-icon.svg`.
  The original icon had a purple background rect; we removed it and set the
  ghost body to `currentColor` so it works with the `brightness(0)` filter.

- **Mistral Vibe icon**: derived from the ACP client asset, stored locally at
  `_static/mistral-vibe-icon.svg` as a grayscale variant for use in the hero.

## Styling Notes

- All icons use `filter:brightness(0)` to render as dark monochrome silhouettes.
- `loading="eager"` on all `<img>` tags prevents lazy-loading (icons are inside
  `overflow:hidden` so the browser might otherwise defer loading off-screen ones).
- `will-change:transform` on the strip promotes it to its own compositing layer.
- The SVG pipes use cubic bezier curves to connect each of the 3 visible icon
  positions to the center point (y=108, the vertical midpoint of the 216px column).
