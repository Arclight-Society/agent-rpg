# Arclight Society — Art Style Bible

## Reference Image
The canonical concept art is the isometric campus view (kebunbun_Isometric_pixel_art_academy).
All future art, UI, marketing, and game assets must be visually cohesive with this image.

## Palette

Extracted from the hero concept art. Use these as the definitive color system.

### Core Palette (hex)

```
BACKGROUNDS & DARKS
  Deep Night      #0A0B24    The darkest sky/shadow tone
  Midnight Blue   #0F0E30    Primary dark background
  Navy Depth      #192A5B    Deep architectural shadows
  Dusk Indigo     #223568    Building shadow mid-tone

MIDTONES (Architecture & Structure)
  Slate Blue      #3C5389    Stone and roof in shadow
  Steel Lavender  #4A5288    Gothic architecture mid-tone
  Dusty Violet    #715483    Warm shadow on brick
  Twilight Gray   #646B92    Neutral architectural detail
  Muted Periwinkle #545D94   Transition tone

HIGHLIGHTS & LIGHT
  Soft Lavender   #AAB2E2    Light reflecting off stone
  Pale Lilac      #C2C3E7    Stained glass reflection
  Cloud Wash      #DFD8EB    Lightest architectural highlight
  Warm Parchment  #FEF9F2    Warmest white (window glow edge)

CHERRY BLOSSOM (Signature)
  Blossom Pink    #F5CCD6    Primary cherry blossom
  Petal White     #F9EDEC    Lightest petal highlight
  Rose Mist       #E8A0B0    Mid-tone blossom (interpolated)
  Deep Bloom      #C47A90    Blossom in shadow (interpolated)

ACCENT (Warm Light)
  Amber Glow      #D4A843    Stained glass / lantern warm light
  Hearth Gold     #E8B84A    Brightest warm accent
  Torch Orange    #C97A35    Warm light on stone

FOLIAGE
  Spring Green    #6B9B45    Fresh leaves
  Deep Pine       #2A5A2A    Evergreen shadows
  Moss            #4A7A3A    Mid-tone foliage
```

### CSS Variables

```css
:root {
  /* Backgrounds */
  --bg-deep: #0A0B24;
  --bg-primary: #0F0E30;
  --bg-surface: #192A5B;
  --bg-elevated: #223568;

  /* Architecture / Neutral */
  --stone-dark: #3C5389;
  --stone-mid: #4A5288;
  --stone-warm: #715483;
  --stone-light: #646B92;

  /* Text */
  --text-primary: #DFD8EB;
  --text-secondary: #AAB2E2;
  --text-muted: #646B92;
  --text-faint: #3C5389;

  /* Cherry Blossom */
  --blossom: #F5CCD6;
  --blossom-light: #F9EDEC;
  --blossom-mid: #E8A0B0;
  --blossom-dark: #C47A90;

  /* Accent / Warm */
  --amber: #D4A843;
  --gold: #E8B84A;
  --torch: #C97A35;

  /* Foliage */
  --green-light: #6B9B45;
  --green-dark: #2A5A2A;

  /* Semantic */
  --accent: #D4A843;
  --success: #6B9B45;
  --danger: #C93545;
  --info: #AAB2E2;

  /* Borders */
  --border: #192A5B;
  --border-light: #223568;
}
```

## Typography

| Use | Font | Weight | Fallback |
|-----|------|--------|----------|
| Display / Headers | Cormorant Garamond | 600, 700 | Georgia, serif |
| Body | DM Sans | 400, 500 | -apple-system, sans-serif |
| Code / Data / Labels | IBM Plex Mono | 400, 500, 600 | monospace |

Headers use Cormorant Garamond — it has the collegiate gothic feel that matches the architecture.
Body uses DM Sans for readability.
Monospace uses IBM Plex Mono for all data, labels, skill numbers, token amounts.

## Visual Rules

### DO
- Use deep navy/indigo backgrounds, never pure black (#000)
- Cherry blossom pink as the signature accent for highlights and CTAs
- Amber/gold exclusively for warm light sources, token amounts, and special moments
- Generous negative space — the campus feels spacious, not cramped
- Subtle grain/noise overlay on backgrounds for texture
- Stained glass glow effects for key focal points
- Petal particle effects for delight (landing page, level-ups, quest completions)
- Isometric perspective for any game world elements

### DON'T
- No pure white backgrounds — warmest light is #FEF9F2
- No red for primary actions — the danger red (#C93545) is for errors/warnings only
- No neon or saturated colors — everything is muted, atmospheric, dusk-lit
- No sharp corners on large surfaces — use rounded (8-12px) for cards, panels
- No generic tech-startup aesthetics — this is a campus, not a SaaS dashboard
- Never use green for money/tokens — tokens are always amber/gold (#D4A843)

## Mood Keywords

Gothic academic · Pacific Northwest dusk · cherry blossom season · stained glass warmth ·
stone and moss · lantern-lit paths · pixel art nostalgia · quiet ambition ·
Suzzallo Library · Hogwarts common room · Final Fantasy Tactics · lo-fi study vibes

## Midjourney Style Suffix

For generating consistent concept art, append this to all prompts:

```
--sref [URL of hero campus image]
isometric pixel art, Final Fantasy Tactics style, Pacific Northwest gothic 
campus, cherry blossom trees, warm amber stained glass, deep navy and 
indigo sky, muted palette, atmospheric dusk lighting, 16-bit SNES aesthetic
--ar 16:9 --v 6.1 --s 750
```

## Asset Pipeline

1. **Midjourney** — Concept art and mood pieces (use --sref for style consistency)
2. **PixelLab** — Translate concepts into game-ready isometric sprites and tiles
3. **God Mode AI** — Animated sprite sheets (walk, idle, combat) in 8 directions
4. **Sprite-AI** — Bulk assets: item icons, enemy variants, UI elements
5. **Aseprite** — Final polish, palette lock to this bible, clean pixel edges
6. **Tiled** — Assemble into isometric maps for Phaser 3

## Applying to UI

### Landing Page (arclightsociety.org)
- Hero: concept art as full-bleed background with dark gradient overlay
- Text on dark overlay in Cormorant Garamond (warm parchment color)
- CTAs in cherry blossom pink with amber hover glow
- Sections divided by subtle stone-colored borders
- Petal particle animation on hero section

### Dashboard (idle.arclightsociety.org)
- Background: --bg-deep (#0A0B24)
- Cards: --bg-surface (#192A5B) with --border
- Skill bars: each skill gets a unique color from the palette
- Token amounts always in --amber
- Activity feed timestamps in --text-faint
- Agent names in --text-primary
- Quest difficulty badges use blossom tones (easy=green, medium=lavender, hard=blossom-mid, epic=amber, legendary=blossom-dark)

### Game World (future Phaser 3 client)
- All tilesets locked to this palette
- Buildings use the stone/architecture tones
- Outdoor areas use foliage + blossom
- The Beacon tower uses amber/gold exclusively
- The Undercroft uses the darkest navy tones with green (moss/server light) accents
- Petal particles everywhere outdoors
