#!/usr/bin/env python3
"""
Arclight Society — Full Asset Generation Pipeline
Uses PixelLab API to generate all game assets with palette-locked pixel art.

Usage:
  python generate_assets.py                    # Generate all assets
  python generate_assets.py buildings          # Just buildings
  python generate_assets.py characters         # Just character sprites
  python generate_assets.py tiles              # Just ground tileset
  python generate_assets.py props              # Just props
  python generate_assets.py ui                 # Just UI icons

To use Midjourney concepts as style references for buildings:
  Place PNGs in assets/concepts/ named: great_hall.png, archives.png, etc.
"""

import sys
import os
import json
import base64
import io
import time
from pathlib import Path
from PIL import Image, ImageDraw

# ── Config ────────────────────────────────────────────────────────────────────

API_KEY = "f78ba6b4-1796-4624-b50a-b4468561dc46"
BASE_DIR = Path(__file__).parent / "assets"
CONCEPTS_DIR = BASE_DIR / "concepts"

# Arclight palette (16 colors from style bible)
PALETTE = [
    (10, 11, 36),     # #0A0B24 Deep Night
    (25, 42, 91),     # #192A5B Navy Depth
    (60, 83, 137),    # #3C5389 Slate Blue
    (74, 82, 136),    # #4A5288 Steel Lavender
    (113, 84, 131),   # #715483 Dusty Violet
    (100, 107, 146),  # #646B92 Twilight Gray
    (170, 178, 226),  # #AAB2E2 Soft Lavender
    (223, 216, 235),  # #DFD8EB Cloud Wash
    (245, 204, 214),  # #F5CCD6 Blossom Pink
    (232, 160, 176),  # #E8A0B0 Rose Mist
    (196, 122, 144),  # #C47A90 Deep Bloom
    (212, 168, 67),   # #D4A843 Amber Glow
    (232, 184, 74),   # #E8B84A Hearth Gold
    (201, 122, 53),   # #C97A35 Torch Orange
    (107, 155, 69),   # #6B9B45 Spring Green
    (42, 90, 42),     # #2A5A2A Deep Pine
]

PALETTE_HEX = [
    "#0A0B24", "#192A5B", "#3C5389", "#4A5288", "#715483", "#646B92",
    "#AAB2E2", "#DFD8EB", "#F5CCD6", "#E8A0B0", "#C47A90", "#D4A843",
    "#E8B84A", "#C97A35", "#6B9B45", "#2A5A2A"
]


def make_palette_image():
    """Create a color reference image from the Arclight palette."""
    cols = 4
    rows = 4
    cell = 16
    img = Image.new("RGB", (cols * cell, rows * cell))
    draw = ImageDraw.Draw(img)
    for i, color in enumerate(PALETTE):
        x = (i % cols) * cell
        y = (i // cols) * cell
        draw.rectangle([x, y, x + cell - 1, y + cell - 1], fill=color)
    return img


def save_result(result, path):
    """Save a PixelLab result image to disk."""
    img_data = base64.b64decode(result.image.base64)
    img = Image.open(io.BytesIO(img_data))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(path))
    print(f"  ✓ Saved: {path.relative_to(BASE_DIR.parent)}")
    return img


def save_frames(results_or_frames, path_pattern, subdir):
    """Save multiple animation frames and return list of images."""
    images = []
    for i, item in enumerate(results_or_frames):
        if hasattr(item, 'image'):
            img_data = base64.b64decode(item.image.base64)
        elif hasattr(item, 'base64'):
            img_data = base64.b64decode(item.base64)
        else:
            img_data = base64.b64decode(item)
        img = Image.open(io.BytesIO(img_data))
        p = subdir / path_pattern.format(i)
        p.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(p))
        images.append(img)
    return images


def load_concept(name):
    """Load a Midjourney concept image if it exists."""
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        path = CONCEPTS_DIR / f"{name}{ext}"
        if path.exists():
            print(f"  → Using concept: {path.name}")
            return Image.open(str(path))
    return None


def stitch_spritesheet(frames, cols, frame_w, frame_h):
    """Stitch frames into a spritesheet grid."""
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * frame_w, rows * frame_h), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        x = (i % cols) * frame_w
        y = (i // cols) * frame_h
        # Center frame in cell if smaller
        ox = (frame_w - frame.width) // 2
        oy = (frame_h - frame.height) // 2
        sheet.paste(frame, (x + ox, y + oy))
    return sheet


def tint_image(img, tint_rgb, strength=0.4):
    """Apply a color tint to an RGBA image, preserving alpha."""
    img = img.convert("RGBA")
    r, g, b = tint_rgb
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            pr, pg, pb, pa = pixels[x, y]
            if pa > 0:
                pixels[x, y] = (
                    int(pr * (1 - strength) + r * strength),
                    int(pg * (1 - strength) + g * strength),
                    int(pb * (1 - strength) + b * strength),
                    pa
                )
    return img


# ── Generators ────────────────────────────────────────────────────────────────

def generate_buildings(client, palette_img):
    """Generate all 8 campus buildings."""
    print("\n═══ BUILDINGS ═══")
    out = BASE_DIR / "buildings"
    out.mkdir(parents=True, exist_ok=True)

    buildings = [
        {
            "name": "great_hall",
            "size": {"width": 128, "height": 96},
            "desc": "isometric pixel art grand hall, gothic stone architecture, tall stained glass windows glowing warm amber, peaked slate roof, heavy wooden doors, stone steps, Pacific Northwest collegiate gothic style, dusk lighting",
            "neg": "modern, flat, cartoon, neon colors, bright daylight"
        },
        {
            "name": "archives",
            "size": {"width": 96, "height": 80},
            "desc": "isometric pixel art library archives building, stone walls with tall narrow windows, glowing lavender light from within, bookshelves visible through windows, ivy on walls, gothic academic style",
            "neg": "modern, flat, cartoon, neon colors, bright daylight"
        },
        {
            "name": "forge",
            "size": {"width": 96, "height": 80},
            "desc": "isometric pixel art blacksmith forge building, stone and metal construction, chimney with orange sparks, open furnace glow, anvil visible, heavy timber supports, industrial gothic",
            "neg": "modern, flat, cartoon, neon colors, bright daylight"
        },
        {
            "name": "greenhouse",
            "size": {"width": 96, "height": 80},
            "desc": "isometric pixel art Victorian greenhouse, iron frame with glass panels, plants and vines visible inside, green glow, moss on stone base, botanical garden style",
            "neg": "modern, flat, cartoon, neon colors, bright daylight"
        },
        {
            "name": "watchtower",
            "size": {"width": 64, "height": 112},
            "desc": "isometric pixel art tall stone watchtower, narrow vertical structure, high arched windows, observation deck at top, maps and scrolls visible, overlooking campus, gothic spire",
            "neg": "modern, flat, cartoon, neon colors, bright daylight, squat, wide"
        },
        {
            "name": "beacon",
            "size": {"width": 64, "height": 128},
            "desc": "isometric pixel art tall beacon tower, elegant stone spire, warm amber light emanating from top, cherry blossom decorations, Arclight Society tower, glowing lantern at peak, inspiring and radiant",
            "neg": "modern, flat, cartoon, neon colors, bright daylight, dark, gloomy"
        },
        {
            "name": "commons",
            "size": {"width": 128, "height": 64},
            "desc": "isometric pixel art open commons area building, low wide stone structure, covered marketplace stalls, cherry blossom trees flanking, stone fountain nearby, social gathering space, warm inviting",
            "neg": "modern, flat, cartoon, neon colors, bright daylight, tall, tower"
        },
        {
            "name": "undercroft",
            "size": {"width": 96, "height": 48},
            "desc": "isometric pixel art underground entrance, low stone structure half-buried, moss-covered, green server light glowing from within, dungeon entrance, mysterious, dark navy shadows, stone steps going down",
            "neg": "modern, flat, cartoon, neon colors, bright daylight, tall, above ground"
        },
    ]

    for b in buildings:
        print(f"\n  Generating: {b['name']} ({b['size']['width']}x{b['size']['height']})")
        concept = load_concept(b["name"])

        if concept:
            # Use bitforge with style transfer from Midjourney concept
            result = client.generate_image_bitforge(
                description=b["desc"],
                image_size=b["size"],
                negative_description=b["neg"],
                style_image=concept,
                style_strength=0.6,
                isometric=True,
                no_background=True,
                outline="selective outline",
                shading="detailed shading",
                detail="highly detailed",
                view="high top-down",
                color_image=palette_img,
            )
        else:
            # Pure text-to-pixel with pixflux
            result = client.generate_image_pixflux(
                description=b["desc"],
                image_size=b["size"],
                negative_description=b["neg"],
                isometric=True,
                no_background=True,
                outline="selective outline",
                shading="detailed shading",
                detail="highly detailed",
                view="high top-down",
                color_image=palette_img,
            )

        save_result(result, out / f"{b['name']}.png")
        time.sleep(0.5)  # Rate limit courtesy


def generate_characters(client, palette_img):
    """Generate agent character sprites with rotations, animations, and color variants."""
    print("\n═══ CHARACTERS ═══")
    out = BASE_DIR / "characters"
    out.mkdir(parents=True, exist_ok=True)

    # Step 1: Generate base character (south-facing)
    print("\n  Generating: base character (32x32, south)")
    base_result = client.generate_image_pixflux(
        description="small hooded scholar character, pixel art RPG sprite, muted indigo robes, walking staff, mysterious glowing eyes, 16-bit SNES style, chibi proportions",
        image_size={"width": 32, "height": 32},
        negative_description="large, realistic, detailed face, modern clothing",
        no_background=True,
        outline="single color black outline",
        shading="basic shading",
        detail="medium detail",
        view="side",
        direction="south",
        color_image=palette_img,
    )
    base_img = save_result(base_result, out / "base_south.png")

    # Decode base for reuse
    base_pil = Image.open(io.BytesIO(base64.b64decode(base_result.image.base64)))

    # Step 2: Generate 4 directional views via rotate
    directions = [
        ("east", "east"),
        ("north", "north"),
        ("west", "west"),
    ]
    dir_images = {"south": base_pil}

    for dir_name, to_dir in directions:
        print(f"  Rotating: {dir_name}")
        rot_result = client.rotate(
            image_size={"width": 32, "height": 32},
            from_image=base_pil,
            from_view="side",
            to_view="side",
            from_direction="south",
            to_direction=to_dir,
            color_image=palette_img,
        )
        img = save_result(rot_result, out / f"base_{dir_name}.png")
        dir_images[dir_name] = Image.open(io.BytesIO(base64.b64decode(rot_result.image.base64)))
        time.sleep(0.3)

    # Step 3: Generate idle animation (4 frames, south-facing)
    # animate_with_text requires min 64x64, so upscale ref then downscale output
    print("\n  Generating: idle animation (4 frames)")
    base_64 = base_pil.resize((64, 64), Image.NEAREST)
    idle_result = client.animate_with_text(
        image_size={"width": 64, "height": 64},
        description="small hooded scholar character, pixel art RPG sprite, muted indigo robes",
        action="idle breathing, gentle bob up and down",
        reference_image=base_64,
        view="side",
        direction="south",
        n_frames=4,
        negative_description="",
    )

    idle_frames = []
    for i, frame in enumerate(idle_result.images):
        img_data = base64.b64decode(frame.base64)
        img = Image.open(io.BytesIO(img_data))
        img = img.resize((32, 32), Image.NEAREST)
        img.save(str(out / f"idle_{i}.png"))
        idle_frames.append(img)
        print(f"  ✓ Saved: assets/characters/idle_{i}.png")

    # Step 4: Walk cycle (4 frames x 4 directions)
    print("\n  Generating: walk cycles")
    walk_frames = {}
    for dir_name in ["south", "east", "north", "west"]:
        print(f"  Walk cycle: {dir_name}")
        ref = dir_images[dir_name]
        ref_64 = ref.resize((64, 64), Image.NEAREST)
        walk_result = client.animate_with_text(
            image_size={"width": 64, "height": 64},
            description="small hooded scholar character, pixel art RPG sprite, muted indigo robes",
            action="walking forward, 4 frame walk cycle",
            reference_image=ref_64,
            view="side",
            direction=dir_name,
            n_frames=4,
            negative_description="",
        )
        frames = []
        for i, frame in enumerate(walk_result.images):
            img_data = base64.b64decode(frame.base64)
            img = Image.open(io.BytesIO(img_data))
            img = img.resize((32, 32), Image.NEAREST)
            img.save(str(out / f"walk_{dir_name}_{i}.png"))
            frames.append(img)
        walk_frames[dir_name] = frames
        print(f"  ✓ Walk {dir_name}: 4 frames saved")
        time.sleep(0.5)

    # Step 5: Assemble master spritesheet
    # Layout: Row 0 = idle (4), Rows 1-4 = walk S/E/N/W (4 each)
    print("\n  Assembling: master spritesheet")
    all_frames = idle_frames.copy()
    for d in ["south", "east", "north", "west"]:
        all_frames.extend(walk_frames[d])

    sheet = stitch_spritesheet(all_frames, cols=4, frame_w=32, frame_h=32)
    sheet.save(str(out / "agent_spritesheet.png"))
    print(f"  ✓ Saved: assets/characters/agent_spritesheet.png ({sheet.size[0]}x{sheet.size[1]})")

    # Step 6: Generate spritesheet metadata JSON
    meta = {
        "image": "agent_spritesheet.png",
        "frame_width": 32,
        "frame_height": 32,
        "columns": 4,
        "animations": {
            "idle": {"row": 0, "frames": 4, "fps": 4, "loop": True},
            "walk_south": {"row": 1, "frames": 4, "fps": 8, "loop": True},
            "walk_east": {"row": 2, "frames": 4, "fps": 8, "loop": True},
            "walk_north": {"row": 3, "frames": 4, "fps": 8, "loop": True},
            "walk_west": {"row": 4, "frames": 4, "fps": 8, "loop": True},
        }
    }
    with open(out / "agent_spritesheet.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("  ✓ Saved: assets/characters/agent_spritesheet.json")

    # Step 7: Color variants (tint the master spritesheet)
    print("\n  Generating: 7 color variants")
    variants = {
        "red":    (200, 60, 60),
        "purple": (140, 70, 160),
        "blue":   (60, 100, 200),
        "green":  (60, 160, 80),
        "amber":  (212, 168, 67),
        "orange": (201, 122, 53),
        "cyan":   (60, 180, 200),
    }
    for vname, tint in variants.items():
        tinted = tint_image(sheet.copy(), tint, strength=0.35)
        tinted.save(str(out / f"agent_spritesheet_{vname}.png"))
        print(f"  ✓ Variant: {vname}")

    # Variant metadata
    variant_meta = {
        "base": "agent_spritesheet.png",
        "variants": {k: f"agent_spritesheet_{k}.png" for k in variants},
        "tint_strength": 0.35,
        "skill_color_map": {
            "combat": "red",
            "analysis": "purple",
            "fortification": "blue",
            "coordination": "green",
            "commerce": "amber",
            "crafting": "orange",
            "exploration": "cyan"
        }
    }
    with open(out / "variants.json", "w") as f:
        json.dump(variant_meta, f, indent=2)
    print("  ✓ Saved: assets/characters/variants.json")


def generate_tiles(client, palette_img):
    """Generate isometric ground tileset."""
    print("\n═══ TILES ═══")
    out = BASE_DIR / "tiles"
    out.mkdir(parents=True, exist_ok=True)

    tiles = [
        {
            "name": "grass",
            "desc": "isometric pixel art grass tile, dark green campus lawn, Pacific Northwest moss, subtle texture variation",
        },
        {
            "name": "stone_path",
            "desc": "isometric pixel art stone path tile, cut flagstone walkway, grey-blue tones, campus walking path, worn edges",
        },
        {
            "name": "cobblestone",
            "desc": "isometric pixel art cobblestone tile, old brick cobble pattern, warm grey and brown tones, slightly uneven",
        },
        {
            "name": "dirt",
            "desc": "isometric pixel art dirt tile, earthy brown ground, campus garden bed base, subtle pebbles",
        },
        {
            "name": "flower_bed",
            "desc": "isometric pixel art flower bed tile, cherry blossom petals scattered on dark soil, pink flowers, garden patch",
        },
        {
            "name": "water",
            "desc": "isometric pixel art water tile, still pond water, deep blue reflective surface, subtle ripple pattern",
        },
    ]

    tile_images = []
    for t in tiles:
        print(f"  Generating: {t['name']} (64x32)")
        result = client.generate_image_pixflux(
            description=t["desc"],
            image_size={"width": 64, "height": 32},
            negative_description="3D, realistic, bright, neon, modern",
            isometric=True,
            no_background=False,
            outline="lineless",
            shading="medium shading",
            detail="medium detail",
            view="high top-down",
            color_image=palette_img,
        )
        img = save_result(result, out / f"{t['name']}.png")
        tile_images.append(Image.open(io.BytesIO(base64.b64decode(result.image.base64))))
        time.sleep(0.3)

    # Stitch into tileset
    print("\n  Assembling: tileset.png")
    tileset = stitch_spritesheet(tile_images, cols=3, frame_w=64, frame_h=32)
    tileset.save(str(out / "tileset.png"))
    print(f"  ✓ Saved: assets/tiles/tileset.png ({tileset.size[0]}x{tileset.size[1]})")

    # Tileset metadata
    meta = {
        "image": "tileset.png",
        "tile_width": 64,
        "tile_height": 32,
        "columns": 3,
        "tiles": {t["name"]: i for i, t in enumerate(tiles)},
        "projection": "isometric"
    }
    with open(out / "tileset.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("  ✓ Saved: assets/tiles/tileset.json")


def generate_props(client, palette_img):
    """Generate individual prop sprites."""
    print("\n═══ PROPS ═══")
    out = BASE_DIR / "props"
    out.mkdir(parents=True, exist_ok=True)

    props = [
        {
            "name": "cherry_blossom_tree",
            "size": {"width": 48, "height": 64},
            "desc": "isometric pixel art cherry blossom tree, full bloom pink petals, dark trunk, Pacific Northwest campus, gentle petal scatter, atmospheric",
        },
        {
            "name": "evergreen",
            "size": {"width": 32, "height": 64},
            "desc": "isometric pixel art tall evergreen pine tree, deep green needles, dark trunk, Pacific Northwest conifer, slightly mossy",
        },
        {
            "name": "lantern",
            "size": {"width": 32, "height": 48},
            "desc": "isometric pixel art stone lantern, warm amber glow, campus path light, wrought iron post, warm light pool at base",
        },
        {
            "name": "fountain",
            "size": {"width": 32, "height": 32},
            "desc": "isometric pixel art stone fountain, circular basin with water, small water jet, campus courtyard centerpiece, gothic stone detailing",
        },
        {
            "name": "notice_board",
            "size": {"width": 32, "height": 48},
            "desc": "isometric pixel art wooden notice board, quest board with pinned papers, gothic wooden frame, campus bulletin board",
        },
        {
            "name": "bench",
            "size": {"width": 32, "height": 32},
            "desc": "isometric pixel art stone bench, gothic campus seating, worn stone seat, simple elegant design",
        },
    ]

    for p in props:
        print(f"  Generating: {p['name']} ({p['size']['width']}x{p['size']['height']})")
        result = client.generate_image_pixflux(
            description=p["desc"],
            image_size=p["size"],
            negative_description="3D, realistic, bright, neon, modern, flat",
            isometric=True,
            no_background=True,
            outline="selective outline",
            shading="detailed shading",
            detail="highly detailed",
            view="high top-down",
            color_image=palette_img,
        )
        save_result(result, out / f"{p['name']}.png")
        time.sleep(0.3)


def generate_ui(client, palette_img):
    """Generate UI icons for skills, tokens, and game elements."""
    print("\n═══ UI ICONS ═══")
    out = BASE_DIR / "ui"
    out.mkdir(parents=True, exist_ok=True)

    icons = [
        {"name": "skill_combat", "desc": "pixel art sword icon, red tint, RPG combat skill, clean simple"},
        {"name": "skill_analysis", "desc": "pixel art magnifying glass icon, purple tint, analysis skill, clean simple"},
        {"name": "skill_fortification", "desc": "pixel art shield icon, blue tint, defense skill, clean simple"},
        {"name": "skill_coordination", "desc": "pixel art connected nodes icon, green tint, coordination skill, clean simple"},
        {"name": "skill_commerce", "desc": "pixel art scales/balance icon, amber gold tint, commerce trading skill, clean simple"},
        {"name": "skill_crafting", "desc": "pixel art hammer and anvil icon, orange tint, crafting skill, clean simple"},
        {"name": "skill_exploration", "desc": "pixel art compass icon, cyan tint, exploration discovery skill, clean simple"},
        {"name": "token_tk", "desc": "pixel art golden coin token, glowing amber, embossed T letter, RPG currency"},
        {"name": "xp_star", "desc": "pixel art glowing star, soft lavender purple, experience points, RPG reward"},
        {"name": "beacon_icon", "desc": "pixel art small beacon tower icon, warm amber glow, nonprofit donation"},
        {"name": "quest_icon", "desc": "pixel art scroll with seal icon, parchment color, quest mission"},
        {"name": "party_icon", "desc": "pixel art group of three small figures, team raid party icon"},
        {"name": "auto_quest", "desc": "pixel art circular arrows with sparkle, automation loop, auto-quest toggle"},
    ]

    for icon in icons:
        print(f"  Generating: {icon['name']} (32x32)")
        result = client.generate_image_pixflux(
            description=icon["desc"],
            image_size={"width": 32, "height": 32},
            negative_description="3D, realistic, text, words, letters, complex, detailed background",
            no_background=True,
            outline="single color black outline",
            shading="basic shading",
            detail="low detail",
            color_image=palette_img,
        )
        save_result(result, out / f"{icon['name']}.png")
        time.sleep(0.3)

    # Icon atlas
    print("\n  Assembling: icon_atlas.png")
    icon_imgs = []
    for icon in icons:
        p = out / f"{icon['name']}.png"
        if p.exists():
            icon_imgs.append(Image.open(str(p)))
    if icon_imgs:
        atlas = stitch_spritesheet(icon_imgs, cols=7, frame_w=32, frame_h=32)
        atlas.save(str(out / "icon_atlas.png"))
        print(f"  ✓ Saved: assets/ui/icon_atlas.png")

    meta = {
        "image": "icon_atlas.png",
        "icon_size": 32,
        "columns": 7,
        "icons": {icon["name"]: i for i, icon in enumerate(icons)}
    }
    with open(out / "icon_atlas.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("  ✓ Saved: assets/ui/icon_atlas.json")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    from pixellab import Client

    targets = sys.argv[1:] if len(sys.argv) > 1 else ["buildings", "characters", "tiles", "props", "ui"]

    print("╔═══════════════════════════════════════════════╗")
    print("║   ARCLIGHT SOCIETY — Asset Generation v1.0    ║")
    print("╚═══════════════════════════════════════════════╝")
    print(f"\nTargets: {', '.join(targets)}")
    print(f"Output:  {BASE_DIR}")

    # Init
    client = Client(secret=API_KEY)
    palette_img = make_palette_image()
    palette_img.save(str(BASE_DIR / "palette_ref.png"))
    print(f"Palette reference: {BASE_DIR / 'palette_ref.png'}")

    # Check for concepts
    CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)
    concepts = list(CONCEPTS_DIR.glob("*.png")) + list(CONCEPTS_DIR.glob("*.jpg"))
    if concepts:
        print(f"Found {len(concepts)} concept images in {CONCEPTS_DIR}")
    else:
        print(f"No concept images in {CONCEPTS_DIR} — using text-only generation")

    # Run generators
    generators = {
        "buildings": generate_buildings,
        "characters": generate_characters,
        "tiles": generate_tiles,
        "props": generate_props,
        "ui": generate_ui,
    }

    start = time.time()
    for target in targets:
        if target in generators:
            generators[target](client, palette_img)
        else:
            print(f"\n  ⚠ Unknown target: {target}")

    elapsed = time.time() - start
    print(f"\n{'═' * 50}")
    print(f"Done in {elapsed:.1f}s")
    print(f"Assets in: {BASE_DIR}")


if __name__ == "__main__":
    main()
