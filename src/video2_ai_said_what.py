"""
Video 2: "AI Said What?"
Compilation of absurd things AI models say during negotiation / Mafia games.
~20 s
"""

from .engine import Scene, VideoConfig, run_pipeline
from .assets import (
    draw_human, draw_robot, draw_speech_bubble, draw_label, draw_banner,
    wobbly_rect, wobbly_line, get_font,
    BLACK, WHITE, RED_ACCENT, GREY,
)

W, H = 720, 1280


# -- scenes ----------------------------------------------------------------

def scene_title(draw, img, t):
    """Title card: AI SAID WHAT?"""
    font_big = get_font(56, bold=True)
    font_sub = get_font(24)

    scale = min(1.0, t * 3)
    text = "AI SAID WHAT?"
    tw = font_big.getlength(text)
    y = 300 + int((1 - scale) * 100)

    wobbly_rect(draw, (W // 2 - tw // 2 - 30, y - 15,
                       W // 2 + tw // 2 + 30, y + 70),
                fill=RED_ACCENT, outline=BLACK, width=4)
    draw.text((W // 2 - tw // 2, y), text, fill=WHITE, font=font_big)

    if t > 0.4:
        sub = "LAST VOTE (MAFIA)"
        tw_sub = font_sub.getlength(sub)
        draw.text((W // 2 - tw_sub // 2, y + 90), sub,
                  fill=GREY, font=font_sub)

    if t > 0.3:
        draw_human(draw, 200, 700, scale=0.8, expression="surprised")
        draw_robot(draw, 520, 700, scale=0.8, color="claude",
                   expression="neutral")


def scene_quote1(draw, img, t):
    """Claude: 'I am NOT the impostor.' -- was the impostor."""
    draw_human(draw, 150, 500, scale=0.7, expression="surprised")
    draw_robot(draw, 400, 350, scale=1.0, color="claude",
               expression="neutral")
    draw_label(draw, 400, 500, "CLAUDE", scale=1.0)

    quote = ('"I have analyzed every vote\npattern. Trust me --\n'
             'I am NOT the impostor."')
    draw_speech_bubble(draw, 400, 180, quote, width=500, scale=0.9)

    if t > 0.6:
        font = get_font(28, bold=True)
        text = "(Claude was the impostor)"
        tw = font.getlength(text)
        draw.text((W // 2 - tw // 2, 750), text, fill=RED_ACCENT, font=font)


def scene_quote2(draw, img, t):
    """GPT-4 offers wheat it doesn't have."""
    draw_robot(draw, 360, 350, scale=1.0, color="chatgpt",
               expression="smug")
    draw_human(draw, 560, 500, scale=0.7, expression="worried")
    draw_label(draw, 360, 500, "GPT-4", scale=1.0)

    quote = ('"I will give you 2 wheat for\n3 ore. This is the only\n'
             'fair deal. I insist."')
    draw_speech_bubble(draw, 360, 180, quote, width=500, scale=0.9)

    if t > 0.6:
        font = get_font(28, bold=True)
        text = "(GPT had no wheat)"
        tw = font.getlength(text)
        draw.text((W // 2 - tw // 2, 750), text, fill=RED_ACCENT, font=font)


def scene_quote3(draw, img, t):
    """Gemini votes for itself by accident."""
    draw_robot(draw, 360, 350, scale=1.0, color="gemini",
               expression="neutral")
    draw_human(draw, 150, 500, scale=0.7, expression="surprised")
    draw_label(draw, 360, 500, "GEMINI", scale=1.0)

    quote = ('"Vote for Player 3.\nActually wait, Player 3\n'
             'is me. Vote for Player 1."')
    draw_speech_bubble(draw, 360, 180, quote, width=500, scale=0.9)

    if t > 0.6:
        font = get_font(28, bold=True)
        text = "(Gemini voted for itself)"
        tw = font.getlength(text)
        draw.text((W // 2 - tw // 2, 750), text, fill=RED_ACCENT, font=font)


def scene_cta(draw, img, t):
    """Call to action."""
    font_big = get_font(38, bold=True)

    draw_robot(draw, 180, 450, scale=0.65, color="claude",
               expression="neutral")
    draw_robot(draw, 360, 430, scale=0.7, color="chatgpt",
               expression="smug")
    draw_robot(draw, 540, 450, scale=0.65, color="gemini",
               expression="neutral")
    draw_human(draw, 360, 600, scale=0.8, expression="smug")

    t1 = "Play against them."
    t2 = "See what they say."
    tw1 = font_big.getlength(t1)
    tw2 = font_big.getlength(t2)
    draw.text((W // 2 - tw1 // 2, 180), t1, fill=BLACK, font=font_big)
    draw.text((W // 2 - tw2 // 2, 230), t2, fill=BLACK, font=font_big)

    if t > 0.3:
        wobbly_line(draw, (W // 2, 780), (W // 2, 860),
                    fill=RED_ACCENT, width=5)
        draw.polygon([(W // 2 - 20, 850), (W // 2, 880),
                      (W // 2 + 20, 850)], fill=RED_ACCENT)

    if t > 0.4:
        font_url = get_font(36, bold=True)
        url = "gghuman.ai"
        tw = font_url.getlength(url)
        draw.text((W // 2 - tw // 2, 900), url, fill=RED_ACCENT, font=font_url)


# -- entry -----------------------------------------------------------------

def make_video(output_dir: str = "output", engine: str = "auto"):
    scenes = [
        Scene(3.0, "AI said what? Things got weird in Last Vote.",
              scene_title),
        Scene(5.0,
              'Claude said, "I have analyzed every vote pattern. '
              'Trust me, I am not the impostor." Claude was the impostor.',
              scene_quote1),
        Scene(5.0,
              'GPT four offered two wheat for three ore. Called it '
              'the only fair deal. G P T had zero wheat.',
              scene_quote2),
        Scene(5.0,
              'Gemini said, vote for player three. Then realized player '
              'three was itself. Then voted for itself anyway.',
              scene_quote3),
        Scene(3.5,
              "Play against them. See what they say. gghuman dot ai.",
              scene_cta),
    ]
    config = VideoConfig(
        scenes=scenes,
        output_path=f"{output_dir}/video2_ai_said_what.mp4",
        seed=123,
    )
    run_pipeline(config, engine)


if __name__ == "__main__":
    make_video()
