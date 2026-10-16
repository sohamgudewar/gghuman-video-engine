"""
GGhuman.ai Claymation Asset Library
Programmatic tactile plasticine / clay stop-motion visual engine.
Features volumetric 3D clay shading, specular highlights, beveled plates,
drop shadows, and clay characters with expressive stop-motion aesthetics.
"""

import math
import random
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Plasticine Clay Palette (Curated earthy & saturated stop-motion clay tones)
# ---------------------------------------------------------------------------
CREAM_BG         = (244, 238, 226)   # Studio cyclorama backdrop
STUDIO_BG_TOP    = (247, 242, 232)
STUDIO_BG_MID    = (234, 226, 212)
FLOOR_COLOR      = (214, 206, 192)

BLACK            = (36, 36, 40)      # Charcoal clay
WHITE            = (248, 246, 242)   # Ivory plasticine
GREEN_SKIN       = (112, 178, 82)    # Human green clay head
BLUE_BODY        = (62, 138, 212)    # Human blue clay torso
RED_ACCENT       = (216, 68, 62)     # Crimson / terracotta clay
PURPLE_BODY      = (136, 84, 172)    # Claude purple body
PURPLE_HEAD      = (68, 44, 88)      # Claude dark head
ORANGE_BODY      = (226, 142, 58)    # Gemini warm clay
DARK_GREEN_TABLE = (64, 122, 74)     # Felt green table clay
BROWN_TABLE      = (132, 86, 52)     # Wood bumper rail clay
CHIP_RED         = (205, 65, 58)     # Red clay poker chip
CHIP_BLUE        = (58, 132, 205)    # Blue clay poker chip
CARD_PURPLE      = (142, 116, 172)   # Card back plasticine
GREY             = (148, 152, 158)   # Neutral slate clay
YELLOW_ACCENT    = (240, 185, 45)    # Mustard / gold clay

# ---------------------------------------------------------------------------
# Color & Shading Math Helpers
# ---------------------------------------------------------------------------
def adjust_color(color, factor):
    """Multiply RGB by factor, clamped to [0, 255]."""
    return tuple(max(0, min(255, int(c * factor))) for c in color)

def blend(c1, c2, t):
    """Linear interpolation between two RGB tuples."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

# ---------------------------------------------------------------------------
# Font helpers
# ---------------------------------------------------------------------------
def get_font(size: int = 32, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a font, cascading through common system paths."""
    paths = [
        "arialbd.ttf" if bold else "arial.ttf",
        "segoeuib.ttf" if bold else "segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()

# ---------------------------------------------------------------------------
# Volumetric Clay Primitives
# ---------------------------------------------------------------------------
def draw_clay_shadow(draw, cx, cy, rx, ry, blur_steps=4, base_shade=185):
    """Draw a soft multi-layered studio drop shadow on the table/floor."""
    for i in range(blur_steps, 0, -1):
        spread = i * 3
        factor = (blur_steps - i + 1) / blur_steps
        shade = base_shade - int(35 * factor)
        bbox = (cx - rx - spread, cy - ry - spread // 2,
                cx + rx + spread, cy + ry + spread // 2)
        draw.ellipse(bbox, fill=(shade, shade - 5, shade - 10))

def draw_clay_sphere(draw, cx, cy, rx, ry, base_color):
    """Draw a tactile 3D clay sphere with core shadow, bevel, and specular glint."""
    if rx <= 1 or ry <= 1:
        draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=base_color)
        return

    # 1. Dark bottom-right core shadow (ambient occlusion & form shadow)
    dark_col = adjust_color(base_color, 0.60)
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=dark_col)

    # 2. Main clay body (offset slightly towards top-left studio key light)
    body_inset = max(1, int(min(rx, ry) * 0.08))
    draw.ellipse((cx - rx, cy - ry, cx + rx - body_inset, cy + ry - body_inset),
                 fill=base_color)

    # 3. Soft diffuse lit zone (top-left hemisphere)
    lite_col = adjust_color(base_color, 1.25)
    hx = cx - int(rx * 0.28)
    hy = cy - int(ry * 0.28)
    hrx = max(1, int(rx * 0.58))
    hry = max(1, int(ry * 0.56))
    draw.ellipse((hx - hrx, hy - hry, hx + hrx, hy + hry), fill=lite_col)

    # 4. Plasticine glossy specular glint (smooth reflective highlight)
    spec_col = blend(lite_col, (255, 255, 255), 0.75)
    sx = cx - int(rx * 0.40)
    sy = cy - int(ry * 0.40)
    srx = max(2, int(rx * 0.22))
    sry = max(2, int(ry * 0.20))
    draw.ellipse((sx - srx, sy - sry, sx + srx, sy + sry), fill=spec_col)

    # 5. Hotspot pinpoint highlight
    dot_r = max(1, int(srx * 0.35))
    draw.ellipse((sx - dot_r, sy - dot_r, sx + dot_r, sy + dot_r),
                 fill=(255, 255, 255))

def draw_clay_capsule(draw, p1, p2, radius, base_color):
    """Draw a rounded clay sausage / limb with cylindrical 3D lighting."""
    x1, y1 = p1
    x2, y2 = p2
    dark_col = adjust_color(base_color, 0.62)
    lite_col = adjust_color(base_color, 1.25)

    # Base dark cylinder
    draw.line([p1, p2], fill=dark_col, width=int(radius * 2))
    draw.ellipse((x1 - radius, y1 - radius, x1 + radius, y1 + radius), fill=dark_col)
    draw.ellipse((x2 - radius, y2 - radius, x2 + radius, y2 + radius), fill=dark_col)

    # Main clay body
    in_r = max(1, int(radius * 0.82))
    draw.line([(x1 - 1, y1 - 2), (x2 - 1, y2 - 2)], fill=base_color, width=in_r * 2)
    draw.ellipse((x1 - in_r - 1, y1 - in_r - 2, x1 + in_r - 1, y1 + in_r - 2), fill=base_color)
    draw.ellipse((x2 - in_r - 1, y2 - in_r - 2, x2 + in_r - 1, y2 + in_r - 2), fill=base_color)

    # Top highlight streak
    hi_r = max(1, int(radius * 0.32))
    draw.line([(x1 - 2, y1 - 4), (x2 - 2, y2 - 4)], fill=lite_col, width=hi_r * 2)

def draw_clay_plate(draw, bbox, base_color, radius=14, shadow=True):
    """Draw a thick pressed clay plaque / card with beveled edges and drop shadow."""
    x1, y1, x2, y2 = bbox
    w = x2 - x1
    h = y2 - y1
    if w <= 4 or h <= 4:
        draw.rectangle((x1, y1, x2, y2), fill=base_color)
        return

    radius = max(2, min(radius, min(w, h) // 2))
    dark_col = adjust_color(base_color, 0.62)
    lite_col = adjust_color(base_color, 1.25)

    if shadow:
        draw_clay_shadow(draw, (x1 + x2) // 2 + 3, (y1 + y2) // 2 + 8,
                         (x2 - x1) // 2 + 4, (y2 - y1) // 2 + 4)

    # Dark bottom & right bevel
    draw.rounded_rectangle((x1, y1, x2, y2), radius=radius, fill=dark_col)

    # Insets scaled safely
    pad_x = max(1, min(3, w // 8))
    pad_y = max(1, min(3, h // 8))

    # Light top & left highlight bevel
    draw.rounded_rectangle((x1, y1, max(x1 + 1, x2 - pad_x), max(y1 + 1, y2 - pad_y)),
                           radius=radius, fill=lite_col)
    # Main clay surface
    in_x1 = x1 + pad_x
    in_y1 = y1 + pad_y
    in_x2 = max(in_x1, x2 - pad_x)
    in_y2 = max(in_y1, y2 - pad_y)
    draw.rounded_rectangle((in_x1, in_y1, in_x2, in_y2),
                           radius=max(1, radius - 2), fill=base_color)

# ---------------------------------------------------------------------------
# Backward-Compatible Hand-Rolled Primitives
# ---------------------------------------------------------------------------
def wobbly_line(draw, start, end, fill=BLACK, width=3, wobble=2):
    """Tactile hand-rolled clay strip / seam."""
    p1 = (start[0] + random.uniform(-wobble, wobble),
          start[1] + random.uniform(-wobble, wobble))
    p2 = (end[0] + random.uniform(-wobble, wobble),
          end[1] + random.uniform(-wobble, wobble))
    draw_clay_capsule(draw, p1, p2, max(2, width // 2), fill)

def wobbly_ellipse(draw, bbox, fill=None, outline=BLACK, width=3, wobble=2):
    """Volumetric clay sphere / blob."""
    x1, y1, x2, y2 = bbox
    cx = (x1 + x2) / 2 + random.uniform(-wobble, wobble)
    cy = (y1 + y2) / 2 + random.uniform(-wobble, wobble)
    rx = (x2 - x1) / 2
    ry = (y2 - y1) / 2
    if fill:
        draw_clay_sphere(draw, int(cx), int(cy), int(rx), int(ry), fill)
    elif outline:
        draw.ellipse(bbox, outline=outline, width=width)

def wobbly_rect(draw, bbox, fill=None, outline=BLACK, width=3, wobble=2, radius=0):
    """Beveled plasticine plaque / tile."""
    x1, y1, x2, y2 = bbox
    r = radius if radius > 0 else 12
    if fill:
        draw_clay_plate(draw, (x1, y1, x2, y2), fill, radius=r, shadow=False)
    elif outline:
        draw.rounded_rectangle(bbox, radius=r, outline=outline, width=width)

# ---------------------------------------------------------------------------
# Character: Clay Human (Green sculpted head, blue pear body)
# ---------------------------------------------------------------------------
def draw_human(draw, cx, cy, scale=1.0, expression="neutral"):
    """Draw the stop-motion green-headed, blue-bodied plasticine human puppet.

    Expressions: neutral, surprised, smug, worried.
    """
    s = scale

    # Cast drop shadow on floor / table
    draw_clay_shadow(draw, cx, cy + int(85 * s), int(75 * s), int(22 * s))

    # Clay Body (Pear-shaped plasticine torso)
    body_w, body_h = int(68 * s), int(78 * s)
    draw_clay_sphere(draw, cx, cy + int(36 * s), body_w, body_h, BLUE_BODY)

    # Clay Arms (bent sausage segments)
    # Left arm
    draw_clay_capsule(draw, (cx - int(54 * s), cy + int(20 * s)),
                            (cx - int(78 * s), cy + int(60 * s)), int(14 * s), BLUE_BODY)
    # Left hand (sculpted green clay ball)
    draw_clay_sphere(draw, cx - int(82 * s), cy + int(65 * s), int(16 * s), int(15 * s), GREEN_SKIN)

    # Right arm
    draw_clay_capsule(draw, (cx + int(54 * s), cy + int(20 * s)),
                            (cx + int(78 * s), cy + int(60 * s)), int(14 * s), BLUE_BODY)
    # Right hand
    draw_clay_sphere(draw, cx + int(82 * s), cy + int(65 * s), int(16 * s), int(15 * s), GREEN_SKIN)

    # Clay Neck
    draw_clay_sphere(draw, cx, cy - int(12 * s), int(20 * s), int(14 * s), adjust_color(GREEN_SKIN, 0.8))

    # Clay Head (Smooth rounded green sphere with stop-motion sheen)
    head_r = int(52 * s)
    head_cy = cy - int(65 * s)
    draw_clay_sphere(draw, cx, head_cy, head_r, head_r, GREEN_SKIN)

    # Sculpted Clay Hair Tufts (pinched clay cones on top)
    tufts = [(-int(18 * s), -int(54 * s)), (0, -int(58 * s)), (int(18 * s), -int(54 * s))]
    for tx, ty in tufts:
        draw_clay_sphere(draw, cx + tx, head_cy + ty, int(10 * s), int(15 * s), adjust_color(GREEN_SKIN, 0.75))

    # Clay Eyes (Pressed white clay spheres with glossy bead pupils)
    eye_dx = int(18 * s)
    eye_y = head_cy - int(4 * s)
    eye_r = int(12 * s)

    for side in (-1, 1):
        ex = cx + side * eye_dx
        # Socket indentation
        draw.ellipse((ex - eye_r - 2, eye_y - eye_r - 2, ex + eye_r + 2, eye_y + eye_r + 2),
                     fill=adjust_color(GREEN_SKIN, 0.7))
        # White clay eyeball
        draw_clay_sphere(draw, ex, eye_y, eye_r, eye_r, WHITE)
        # Black bead pupil with glint
        pupil_r = int(5 * s)
        draw.ellipse((ex - pupil_r, eye_y - pupil_r, ex + pupil_r, eye_y + pupil_r), fill=BLACK)
        draw.ellipse((ex - pupil_r + 1, eye_y - pupil_r + 1, ex - pupil_r + 3, eye_y - pupil_r + 3),
                     fill=(255, 255, 255))

    # Clay Eyebrows & Mouth according to expression
    if expression == "worried":
        # Angled worried clay eyebrows
        draw_clay_capsule(draw, (cx - int(28 * s), eye_y - int(18 * s)),
                                (cx - int(8 * s), eye_y - int(24 * s)), int(4 * s), BLACK)
        draw_clay_capsule(draw, (cx + int(8 * s), eye_y - int(24 * s)),
                                (cx + int(28 * s), eye_y - int(18 * s)), int(4 * s), BLACK)
        # Wavy worried clay mouth
        draw_clay_capsule(draw, (cx - int(16 * s), head_cy + int(24 * s)),
                                (cx + int(16 * s), head_cy + int(28 * s)), int(4 * s), BLACK)
    elif expression == "surprised":
        draw_clay_capsule(draw, (cx - int(26 * s), eye_y - int(22 * s)),
                                (cx - int(10 * s), eye_y - int(22 * s)), int(4 * s), BLACK)
        draw_clay_capsule(draw, (cx + int(10 * s), eye_y - int(22 * s)),
                                (cx + int(26 * s), eye_y - int(22 * s)), int(4 * s), BLACK)
        # Open O clay mouth with dark hollow and pink tongue
        draw_clay_sphere(draw, cx, head_cy + int(24 * s), int(11 * s), int(15 * s), BLACK)
        draw_clay_sphere(draw, cx, head_cy + int(28 * s), int(7 * s), int(6 * s), (230, 110, 130))
    elif expression == "smug":
        draw_clay_capsule(draw, (cx - int(26 * s), eye_y - int(16 * s)),
                                (cx - int(10 * s), eye_y - int(24 * s)), int(4 * s), BLACK)
        draw_clay_capsule(draw, (cx + int(10 * s), eye_y - int(20 * s)),
                                (cx + int(26 * s), eye_y - int(18 * s)), int(4 * s), BLACK)
        draw_clay_capsule(draw, (cx - int(14 * s), head_cy + int(26 * s)),
                                (cx + int(18 * s), head_cy + int(18 * s)), int(4 * s), BLACK)
    else: # neutral / gentle smile
        draw_clay_capsule(draw, (cx - int(24 * s), eye_y - int(18 * s)),
                                (cx - int(8 * s), eye_y - int(18 * s)), int(3 * s), BLACK)
        draw_clay_capsule(draw, (cx + int(8 * s), eye_y - int(18 * s)),
                                (cx + int(24 * s), eye_y - int(18 * s)), int(3 * s), BLACK)
        draw_clay_capsule(draw, (cx - int(14 * s), head_cy + int(24 * s)),
                                (cx + int(14 * s), head_cy + int(24 * s)), int(4 * s), BLACK)

# ---------------------------------------------------------------------------
# Character: Clay Robot (Chunky beveled block puppet with LED visor)
# ---------------------------------------------------------------------------
_ROBOT_COLOURS = {
    "chatgpt": {"body": (76, 118, 86), "head": (50, 58, 56), "eyes": (110, 235, 215)},
    "claude":  {"body": PURPLE_BODY, "head": PURPLE_HEAD, "eyes": (225, 205, 245)},
    "gemini":  {"body": ORANGE_BODY, "head": (78, 58, 38), "eyes": (245, 210, 105)},
    "generic": {"body": GREY, "head": (78, 78, 82), "eyes": (160, 230, 160)},
}

def draw_robot(draw, cx, cy, scale=1.0, color="chatgpt", expression="neutral"):
    """Draw an AI robot claymation puppet."""
    s = scale
    c = _ROBOT_COLOURS.get(color, _ROBOT_COLOURS["generic"])

    # Shadow
    draw_clay_shadow(draw, cx, cy + int(85 * s), int(75 * s), int(22 * s))

    # Torso (Chunky beveled clay block)
    body_w, body_h = int(62 * s), int(65 * s)
    bbox_body = (cx - body_w, cy - int(5 * s), cx + body_w, cy + body_h)
    draw_clay_plate(draw, bbox_body, c["body"], radius=int(18 * s), shadow=False)

    # Robot Arms (clay tubes with ball socket joints)
    for sign in (-1, 1):
        p1 = (cx + sign * int(56 * s), cy + int(15 * s))
        p2 = (cx + sign * int(80 * s), cy + int(50 * s))
        draw_clay_capsule(draw, p1, p2, int(13 * s), c["body"])
        draw_clay_sphere(draw, p2[0], p2[1], int(15 * s), int(15 * s), (160, 165, 170))

    # Robot Head (Rounded beveled clay block)
    head_w, head_h = int(48 * s), int(42 * s)
    head_cy = cy - int(60 * s)
    bbox_head = (cx - head_w, head_cy - head_h, cx + head_w, head_cy + head_h)
    draw_clay_plate(draw, bbox_head, c["head"], radius=int(16 * s), shadow=False)

    # Antenna (clay rod with glossy red cherry ball)
    draw_clay_capsule(draw, (cx, head_cy - head_h), (cx, head_cy - head_h - int(24 * s)),
                      int(5 * s), (110, 115, 120))
    draw_clay_sphere(draw, cx, head_cy - head_h - int(32 * s), int(13 * s), int(13 * s), RED_ACCENT)

    # Eyes (Recessed glossy LED visor / twin glass eyes)
    eye_w, eye_h = int(22 * s), int(12 * s)
    for sign in (-1, 1):
        ex = cx + sign * int(22 * s)
        ey = head_cy - int(4 * s)
        draw_clay_plate(draw, (ex - eye_w // 2, ey - eye_h // 2, ex + eye_w // 2, ey + eye_h // 2),
                        c["eyes"], radius=int(6 * s), shadow=False)
        # Specular glint
        draw.ellipse((ex - 3, ey - 3, ex + 2, ey + 2), fill=(255, 255, 255))

    # Robot expression
    if expression == "smug":
        draw_clay_capsule(draw, (cx - int(16 * s), head_cy + int(22 * s)),
                                (cx + int(18 * s), head_cy + int(16 * s)), int(3 * s), c["eyes"])

    # Pressed-in stamped logo on chest
    logo_y = cy + int(26 * s)
    if color == "chatgpt":
        for a in (0, 120, 240):
            lx = cx + int(12 * s * math.cos(math.radians(a)))
            ly = logo_y + int(12 * s * math.sin(math.radians(a)))
            draw.ellipse((lx - 6, ly - 6, lx + 6, ly + 6), outline=(220, 245, 235), width=2)
    elif color == "claude":
        star_s = int(12 * s)
        draw.polygon([
            (cx, logo_y - star_s), (cx + int(4 * s), logo_y - int(4 * s)),
            (cx + star_s, logo_y), (cx + int(4 * s), logo_y + int(4 * s)),
            (cx, logo_y + star_s), (cx - int(4 * s), logo_y + int(4 * s)),
            (cx - star_s, logo_y), (cx - int(4 * s), logo_y - int(4 * s)),
        ], fill=(235, 225, 245))

# ---------------------------------------------------------------------------
# Playing Cards
# ---------------------------------------------------------------------------
def draw_card(draw, cx, cy, value="A", suit="hearts", scale=1.0, face_down=False):
    """Draw a thick, tactile clay playing card."""
    s = scale
    cw, ch = int(52 * s), int(72 * s)
    bbox = (cx - cw, cy - ch, cx + cw, cy + ch)

    if face_down:
        draw_clay_plate(draw, bbox, CARD_PURPLE, radius=int(12 * s), shadow=True)
        font = get_font(int(36 * s), bold=True)
        draw.text((cx - int(12 * s), cy - int(20 * s)), "?", fill=WHITE, font=font)
        return

    draw_clay_plate(draw, bbox, WHITE, radius=int(12 * s), shadow=True)

    col = RED_ACCENT if suit in ("hearts", "diamonds") else BLACK
    font = get_font(int(28 * s), bold=True)
    draw.text((cx - cw + int(12 * s), cy - ch + int(8 * s)), value, fill=col, font=font)

    # Stamped clay suit symbol in center
    sy = cy + int(12 * s)
    if suit == "spades":
        draw_clay_sphere(draw, cx, sy - int(6 * s), int(14 * s), int(16 * s), col)
        draw_clay_capsule(draw, (cx, sy + int(2 * s)), (cx, sy + int(15 * s)), int(4 * s), col)
    elif suit == "hearts":
        draw_clay_sphere(draw, cx - int(7 * s), sy - int(4 * s), int(9 * s), int(9 * s), col)
        draw_clay_sphere(draw, cx + int(7 * s), sy - int(4 * s), int(9 * s), int(9 * s), col)
        draw.polygon([(cx - int(14 * s), sy - int(2 * s)),
                      (cx, sy + int(16 * s)),
                      (cx + int(14 * s), sy - int(2 * s))], fill=col)
    elif suit == "diamonds":
        draw.polygon([(cx, sy - int(14 * s)), (cx + int(10 * s), sy),
                      (cx, sy + int(14 * s)), (cx - int(10 * s), sy)], fill=col)
    elif suit == "clubs":
        for dx, dy in [(-int(6 * s), int(3 * s)), (int(6 * s), int(3 * s)), (0, -int(7 * s))]:
            draw_clay_sphere(draw, cx + dx, sy + dy, int(6 * s), int(6 * s), col)
        draw_clay_capsule(draw, (cx, sy), (cx, sy + int(14 * s)), int(3 * s), col)

# ---------------------------------------------------------------------------
# Game Elements: Poker Table & Chips
# ---------------------------------------------------------------------------
def draw_poker_table(draw, cx, cy, width=600, height=300):
    """Draw an authentic stop-motion clay poker table."""
    w2, h2 = width // 2, height // 2
    # Soft table cast shadow
    draw_clay_shadow(draw, cx, cy + 22, w2 + 25, h2 + 20, blur_steps=4)

    # Wood bumper rail (thick rounded mahogany clay rim)
    draw_clay_plate(draw, (cx - w2, cy - h2, cx + w2, cy + h2),
                    BROWN_TABLE, radius=110, shadow=False)

    # Inner Green Felt (tactile beveled clay insert)
    felt_pad = 22
    draw_clay_plate(draw, (cx - w2 + felt_pad, cy - h2 + felt_pad,
                           cx + w2 - felt_pad, cy + h2 - felt_pad),
                    DARK_GREEN_TABLE, radius=90, shadow=False)

def draw_chip_stack(draw, cx, cy, count=10, scale=1.0):
    """Draw a stack of chunky clay poker chips."""
    s = scale
    cw = max(8, int(26 * s))
    ch = max(3, int(6 * s))
    draw_clay_shadow(draw, cx, cy + int(6 * s), cw + 4, int(8 * s))
    for i in range(count):
        y = cy - i * ch
        col = CHIP_RED if i % 2 == 0 else CHIP_BLUE
        dark_c = adjust_color(col, 0.65)
        lite_c = adjust_color(col, 1.25)
        # Chip rim / 3D thickness
        draw.ellipse((cx - cw, y - int(3 * s) + 2, cx + cw, y + int(3 * s) + 2), fill=dark_c)
        # Chip top face
        draw.ellipse((cx - cw, y - int(3 * s), cx + cw, y + int(3 * s)), fill=col)
        # Top highlight
        draw.ellipse((cx - int(cw * 0.7), y - int(3 * s) + 1,
                      cx + int(cw * 0.7), y + int(3 * s) - 1), fill=lite_c)
        # White edge stripes
        stripe_w = max(2, int(5 * s))
        draw.rectangle((cx - stripe_w, y - int(2 * s), cx + stripe_w, y + int(2 * s)),
                       fill=WHITE)

def draw_speech_bubble(draw, cx, cy, text, width=400, scale=1.0, tail_dir="down"):
    """Draw a molded white clay speech plaque with pointer tail."""
    s = scale
    lines = text.split("\n")
    font = get_font(int(24 * s), bold=True)
    line_h = int(30 * s)
    h = len(lines) * line_h + int(35 * s)
    w = int(width * s)

    bbox = (cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)
    # Clay plaque
    draw_clay_plate(draw, bbox, WHITE, radius=int(18 * s), shadow=True)

    # Clay pointer tail
    if tail_dir == "down":
        tx = cx - int(20 * s)
        ty = cy + h // 2
        draw.polygon([(tx, ty - 2), (tx - int(16 * s), ty + int(24 * s)), (tx + int(16 * s), ty - 2)],
                     fill=WHITE)
        draw.line([(tx - int(16 * s), ty + int(24 * s)), (tx + int(16 * s), ty - 2)],
                  fill=adjust_color(WHITE, 0.7), width=3)

    for i, line in enumerate(lines):
        tw = font.getlength(line)
        draw.text((cx - tw / 2, cy - h // 2 + int(18 * s) + i * line_h),
                  line, fill=BLACK, font=font)

# ---------------------------------------------------------------------------
# Hex board (Settler Rush / Catan style)
# ---------------------------------------------------------------------------
def draw_hex(draw, cx, cy, size, fill_color, outline=BLACK, width=2):
    """Draw a tactile 3D beveled clay hexagon."""
    points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        x = cx + size * math.cos(angle)
        y = cy + size * math.sin(angle)
        points.append((x, y))

    # Base shadow
    draw_clay_shadow(draw, cx, cy + 4, size, int(size * 0.8), blur_steps=2)

    # Shaded hex body
    dark_c = adjust_color(fill_color, 0.7)
    lite_c = adjust_color(fill_color, 1.25)
    draw.polygon(points, fill=dark_c)

    # Highlight facet
    inner_pts = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        x = cx - 1 + int(size * 0.88 * math.cos(angle))
        y = cy - 2 + int(size * 0.88 * math.sin(angle))
        inner_pts.append((x, y))
    draw.polygon(inner_pts, fill=fill_color)

    # Center resource clay token
    draw_clay_sphere(draw, cx, cy, max(3, int(size * 0.22)), max(3, int(size * 0.22)), lite_c)

_HEX_COLOURS = [
    (115, 178, 80),   # wood green
    (230, 185, 55),   # wheat gold
    (155, 160, 165),  # ore slate
    (195, 95, 55),    # brick terracotta
    (135, 195, 75),   # sheep pasture
]

def draw_mini_board(draw, cx, cy, scale=1.0):
    """Draw a Settler Rush hex board in claymation style."""
    s = scale
    hex_size = int(30 * s)
    rows = [
        [(-2, -1), (-1, -1), (0, -1), (1, -1)],
        [(-1.5, 0), (-0.5, 0), (0.5, 0), (1.5, 0)],
        [(-1, 1), (0, 1), (1, 1)],
    ]
    for row in rows:
        for gx, gy in row:
            hx = cx + int(gx * hex_size * 1.72)
            hy = cy + int(gy * hex_size * 1.5)
            draw_hex(draw, hx, hy, hex_size, random.choice(_HEX_COLOURS))

# ---------------------------------------------------------------------------
# UI Badges & Overlays
# ---------------------------------------------------------------------------
def draw_label(draw, cx, cy, text, scale=1.0, bg=WHITE):
    """Small beveled clay badge (e.g. YOUR HAND, AI HAND, CLAUDE)."""
    s = scale
    font = get_font(int(18 * s), bold=True)
    tw = font.getlength(text)
    pad = int(14 * s)
    bbox = (cx - tw / 2 - pad, cy - int(15 * s),
            cx + tw / 2 + pad, cy + int(15 * s))
    draw_clay_plate(draw, bbox, bg, radius=int(10 * s), shadow=True)
    draw.text((cx - tw / 2, cy - int(10 * s)), text, fill=BLACK, font=font)

def draw_banner(draw, x, y, text, scale=1.0):
    """Vibrant crimson clay banner."""
    s = scale
    font = get_font(int(24 * s), bold=True)
    tw = font.getlength(text)
    pad = int(18 * s)
    bbox = (x, y, x + tw + pad * 2, y + int(42 * s))
    draw_clay_plate(draw, bbox, RED_ACCENT, radius=int(12 * s), shadow=True)
    draw.text((x + pad, y + int(8 * s)), text, fill=WHITE, font=font)

def draw_watermark(draw, img_width, img_height):
    """GGhuman branding watermark in bottom-left rendered as a tactile clay badge."""
    x, y = 30, img_height - 165
    draw_clay_plate(draw, (x, y, x + 215, y + 115), WHITE, radius=14, shadow=True)

    font_big = get_font(38, bold=True)
    font_sub = get_font(20, bold=False)

    draw.text((x + 16, y + 12), "GG", fill=RED_ACCENT, font=font_big)
    draw.text((x + 72, y + 12), "human", fill=BLACK, font=font_big)
    draw.text((x + 16, y + 62), "Play vs AI", fill=(80, 80, 85), font=font_sub)
    draw.text((x + 16, y + 84), "gghuman.ai", fill=RED_ACCENT, font=font_sub)

def draw_caption(draw, cx, cy, word, scale=1.0):
    """Dynamic word-by-word synced caption sticker (puffy golden clay badge)."""
    s = scale
    font = get_font(int(36 * s), bold=True)
    tw = font.getlength(word)
    pad_x = int(22 * s)
    pad_y = int(12 * s)

    bbox = (cx - tw / 2 - pad_x, cy - pad_y,
            cx + tw / 2 + pad_x, cy + int(42 * s) + pad_y)
    draw_clay_plate(draw, bbox, YELLOW_ACCENT, radius=int(16 * s), shadow=True)
    draw.text((cx - tw / 2, cy + int(4 * s)), word, fill=BLACK, font=font)

# ---------------------------------------------------------------------------
# Frame Constructor: Studio Stage Cyclorama & Tabletop
# ---------------------------------------------------------------------------
def create_frame(width=720, height=1280):
    """Create a Claymation studio backdrop with smooth cyclorama gradient and tabletop floor."""
    img = Image.new("RGB", (width, height), STUDIO_BG_TOP)
    draw = ImageDraw.Draw(img)

    # Vertical gradient seamless cyclorama backdrop
    horizon = int(height * 0.72)
    for y in range(horizon):
        t = y / horizon
        col = blend(STUDIO_BG_TOP, STUDIO_BG_MID, t)
        draw.line([(0, y), (width, y)], fill=col)

    # Soft horizon blend
    for y in range(horizon, horizon + 25):
        t = (y - horizon) / 25
        col = blend((195, 188, 174), FLOOR_COLOR, t)
        draw.line([(0, y), (width, y)], fill=col)

    # Studio table floor plane
    for y in range(horizon + 25, height):
        t = (y - horizon) / (height - horizon)
        col = blend(FLOOR_COLOR, (200, 192, 178), t * 0.6)
        draw.line([(0, y), (width, y)], fill=col)

    return img
