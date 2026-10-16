"""
Video 1: "Would You Call?"
Interactive poker decision reel -- shows a hand, freezes on the decision,
reveals the AI was bluffing.  ~20 s
"""

import math
import random

from .engine import Scene, VideoConfig, run_pipeline
from .assets import (
    draw_human, draw_robot, draw_card, draw_poker_table, draw_chip_stack,
    draw_speech_bubble, draw_label, draw_banner,
    wobbly_rect, wobbly_line, get_font,
    BLACK, WHITE, RED_ACCENT, BLUE_BODY, GREY,
)

W, H = 720, 1280


# -- scenes ----------------------------------------------------------------

def scene_setup(draw, img, t):
    """Table with human + AI, community cards being dealt."""
    draw_poker_table(draw, 360, 650, width=550, height=280)
    draw_human(draw, 200, 550, scale=0.75, expression="neutral")
    draw_robot(draw, 520, 550, scale=0.75, color="chatgpt", expression="neutral")

    # Community cards (appear progressively)
    cards = [("K", "spades"), ("9", "hearts"), ("4", "clubs"),
             ("J", "diamonds"), ("2", "spades")]
    for i, (val, suit) in enumerate(cards):
        if t > (i + 1) * 0.12:
            x = 220 + i * 70
            draw_card(draw, x, 720, val, suit, scale=0.45)

    # Hole cards
    draw_label(draw, 200, 830, "YOUR HAND", scale=0.8)
    draw_card(draw, 170, 900, "A", "hearts", scale=0.5)
    draw_card(draw, 240, 900, "Q", "diamonds", scale=0.5)
    draw_label(draw, 520, 830, "AI HAND", scale=0.8)
    draw_card(draw, 490, 900, face_down=True, scale=0.5)
    draw_card(draw, 560, 900, face_down=True, scale=0.5)


def scene_allin(draw, img, t):
    """AI shoves all-in."""
    draw_poker_table(draw, 360, 650, width=550, height=280)
    draw_human(draw, 200, 550, scale=0.75, expression="worried")
    draw_robot(draw, 520, 550, scale=0.75, color="chatgpt", expression="smug")

    # Community cards
    for i, (val, suit) in enumerate([("K", "spades"), ("9", "hearts"),
                                      ("4", "clubs"), ("J", "diamonds"),
                                      ("2", "spades")]):
        draw_card(draw, 220 + i * 70, 720, val, suit, scale=0.45)

    # Chip stack + "ALL IN" pulse
    draw_chip_stack(draw, 420, 640, count=12, scale=0.7)
    pulse = 1.0 + 0.15 * math.sin(t * math.pi * 6)
    font = get_font(int(40 * pulse), bold=True)
    text = "ALL IN"
    tw = font.getlength(text)
    draw.text((360 - tw / 2, 420), text, fill=RED_ACCENT, font=font)


def scene_decision(draw, img, t):
    """WOULD YOU CALL? freeze-frame."""
    draw_poker_table(draw, 360, 650, width=550, height=280)
    draw_human(draw, 200, 550, scale=0.75, expression="worried")
    draw_robot(draw, 520, 550, scale=0.75, color="chatgpt", expression="smug")

    for i, (val, suit) in enumerate([("K", "spades"), ("9", "hearts"),
                                      ("4", "clubs"), ("J", "diamonds"),
                                      ("2", "spades")]):
        draw_card(draw, 220 + i * 70, 720, val, suit, scale=0.45)

    # Flashing question
    if int(t * 8) % 2 == 0:
        font = get_font(52, bold=True)
        text = "WOULD YOU CALL?"
        tw = font.getlength(text)
        wobbly_rect(draw, (W // 2 - tw // 2 - 25, 280,
                           W // 2 + tw // 2 + 25, 355),
                    fill=RED_ACCENT, outline=BLACK, width=4)
        draw.text((W // 2 - tw // 2, 288), text, fill=WHITE, font=font)


def scene_reveal(draw, img, t):
    """Reveal: AI had 7-3 offsuit -- pure bluff."""
    draw_poker_table(draw, 360, 650, width=550, height=280)
    draw_human(draw, 200, 550, scale=0.75, expression="surprised")
    draw_robot(draw, 520, 550, scale=0.75, color="chatgpt", expression="neutral")

    for i, (val, suit) in enumerate([("K", "spades"), ("9", "hearts"),
                                      ("4", "clubs"), ("J", "diamonds"),
                                      ("2", "spades")]):
        draw_card(draw, 220 + i * 70, 720, val, suit, scale=0.45)

    # Revealed cards
    draw_card(draw, 490, 900, "7", "clubs", scale=0.55)
    draw_card(draw, 570, 900, "3", "hearts", scale=0.55)
    draw_label(draw, 530, 830, "7-3 OFF", scale=0.9, bg=RED_ACCENT)

    if t > 0.4:
        draw_banner(draw, W // 2 - 120, 300, "PURE BLUFF.", scale=1.2)


def scene_cta(draw, img, t):
    """Call to action."""
    font_big = get_font(36, bold=True)

    draw_human(draw, W // 2, 550, scale=1.0, expression="smug")

    t1 = "Think you'd"
    t2 = "read it better?"
    tw1 = font_big.getlength(t1)
    tw2 = font_big.getlength(t2)
    draw.text((W // 2 - tw1 // 2, 200), t1, fill=BLACK, font=font_big)
    draw.text((W // 2 - tw2 // 2, 250), t2, fill=BLACK, font=font_big)

    if t > 0.3:
        wobbly_line(draw, (W // 2, 750), (W // 2, 830),
                    fill=RED_ACCENT, width=5)
        draw.polygon([(W // 2 - 20, 820), (W // 2, 850),
                      (W // 2 + 20, 820)], fill=RED_ACCENT)

    if t > 0.4:
        font_url = get_font(36, bold=True)
        url = "gghuman.ai"
        tw = font_url.getlength(url)
        draw.text((W // 2 - tw // 2, 870), url, fill=RED_ACCENT, font=font_url)


# -- entry -----------------------------------------------------------------

def make_video(output_dir: str = "output", engine: str = "auto"):
    scenes = [
        Scene(4.0, "You're sitting across from ChatGPT. King nine four on the board.", scene_setup),
        Scene(3.0, "The AI shoves all in.", scene_allin),
        Scene(3.5, "Would you call?", scene_decision),
        Scene(4.0, "The AI had seven three offsuit. Pure bluff.", scene_reveal),
        Scene(3.0, "Think you'd read it better? gghuman dot ai.", scene_cta),
    ]
    config = VideoConfig(
        scenes=scenes,
        output_path=f"{output_dir}/video1_would_you_call.mp4",
        seed=42,
    )
    run_pipeline(config, engine)


if __name__ == "__main__":
    make_video()
