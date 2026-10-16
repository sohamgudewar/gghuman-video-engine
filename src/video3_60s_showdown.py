"""
Video 3: "60 Second Showdown"
Compressed highlight reel of a Settler Rush game -- human vs DeepSeek.
~22 s
"""

from .engine import Scene, VideoConfig, run_pipeline
from .assets import (
    draw_human, draw_robot, draw_mini_board, draw_speech_bubble,
    draw_banner, wobbly_rect, wobbly_line, get_font,
    BLACK, WHITE, RED_ACCENT, BLUE_BODY, GREY,
)

W, H = 720, 1280


# -- helpers ---------------------------------------------------------------

def draw_score_bar(draw, human_score, ai_score, y=120):
    """Score comparison bar across the top."""
    font = get_font(28, bold=True)
    font_sm = get_font(20)

    bar_w, bar_h = 500, 50
    bx = W // 2 - bar_w // 2
    wobbly_rect(draw, (bx, y, bx + bar_w, y + bar_h),
                fill=WHITE, outline=BLACK, width=2)

    human_ratio = human_score / max(human_score + ai_score, 1)
    hw = int(bar_w * human_ratio)
    if hw > 5:
        wobbly_rect(draw, (bx, y, bx + hw, y + bar_h),
                    fill=BLUE_BODY, outline=None)
    if bar_w - hw > 5:
        wobbly_rect(draw, (bx + hw, y, bx + bar_w, y + bar_h),
                    fill=GREY, outline=None)
    wobbly_rect(draw, (bx, y, bx + bar_w, y + bar_h),
                fill=None, outline=BLACK, width=2)

    draw.text((bx + 15, y + 10), str(human_score), fill=WHITE, font=font)
    ai_text = str(ai_score)
    tw = font.getlength(ai_text)
    draw.text((bx + bar_w - tw - 15, y + 10), ai_text,
              fill=WHITE, font=font)

    draw.text((bx, y - 25), "YOU", fill=BLUE_BODY, font=font_sm)
    ai_label = "DeepSeek"
    tw_ai = font_sm.getlength(ai_label)
    draw.text((bx + bar_w - tw_ai, y - 25), ai_label,
              fill=GREY, font=font_sm)


# -- scenes ----------------------------------------------------------------

def scene_title(draw, img, t):
    """60s SHOWDOWN title + VS matchup."""
    font_big = get_font(48, bold=True)
    font_sub = get_font(22)

    text = "60s SHOWDOWN"
    tw = font_big.getlength(text)
    wobbly_rect(draw, (W // 2 - tw // 2 - 25, 240,
                       W // 2 + tw // 2 + 25, 310),
                fill=RED_ACCENT, outline=BLACK, width=4)
    draw.text((W // 2 - tw // 2, 248), text, fill=WHITE, font=font_big)

    sub = "SETTLER RUSH"
    tw_sub = font_sub.getlength(sub)
    draw.text((W // 2 - tw_sub // 2, 330), sub, fill=GREY, font=font_sub)

    draw_human(draw, 230, 550, scale=0.9, expression="neutral")
    font_vs = get_font(36, bold=True)
    draw.text((W // 2 - 20, 540), "VS", fill=RED_ACCENT, font=font_vs)
    draw_robot(draw, 490, 550, scale=0.9, color="generic",
               expression="neutral")

    font_label = get_font(22, bold=True)
    draw.text((195, 680), "YOU", fill=BLACK, font=font_label)
    draw.text((430, 680), "DeepSeek", fill=BLACK, font=font_label)


def scene_early(draw, img, t):
    """Early game: placing first settlements."""
    draw_banner(draw, 30, 60, "EARLY GAME", scale=0.8)
    draw_score_bar(draw, 2, 2, y=130)
    draw_mini_board(draw, W // 2, 450, scale=1.2)
    draw_human(draw, 100, 750, scale=0.55, expression="neutral")
    draw_robot(draw, 620, 750, scale=0.55, color="generic",
               expression="neutral")

    if t > 0.3:
        font = get_font(22, bold=True)
        text = "Both players settle the coast"
        tw = font.getlength(text)
        draw.text((W // 2 - tw // 2, 680), text, fill=BLACK, font=font)


def scene_mid(draw, img, t):
    """Mid game: AI trades aggressively."""
    draw_banner(draw, 30, 60, "MID GAME", scale=0.8)
    draw_score_bar(draw, 4, 5, y=130)
    draw_mini_board(draw, W // 2, 420, scale=1.1)

    draw_robot(draw, 500, 680, scale=0.7, color="generic",
               expression="smug")
    draw_speech_bubble(draw, 430, 590, '"3 for 1?\nFair."',
                       width=200, scale=0.7)
    draw_human(draw, 180, 700, scale=0.65, expression="worried")

    font = get_font(22, bold=True)
    text = "DeepSeek builds 3 roads in one turn"
    tw = font.getlength(text)
    draw.text((W // 2 - tw // 2, 810), text, fill=RED_ACCENT, font=font)


def scene_late(draw, img, t):
    """Late game: neck and neck, final push."""
    draw_banner(draw, 30, 60, "FINAL TURN", scale=0.8)

    human_score = 10 if t > 0.7 else 9
    draw_score_bar(draw, human_score, 9, y=130)
    draw_mini_board(draw, W // 2, 420, scale=1.1)

    if t > 0.7:
        draw_human(draw, 200, 700, scale=0.75, expression="smug")
        draw_robot(draw, 520, 700, scale=0.75, color="generic",
                   expression="neutral")
    else:
        draw_human(draw, 200, 700, scale=0.75, expression="worried")
        draw_robot(draw, 520, 700, scale=0.75, color="generic",
                   expression="smug")

    if t > 0.75:
        font_big = get_font(44, bold=True)
        text = "HUMAN WINS!"
        tw = font_big.getlength(text)
        wobbly_rect(draw, (W // 2 - tw // 2 - 20, 820,
                           W // 2 + tw // 2 + 20, 880),
                    fill=BLUE_BODY, outline=BLACK, width=3)
        draw.text((W // 2 - tw // 2, 828), text, fill=WHITE, font=font_big)


def scene_cta(draw, img, t):
    """Call to action."""
    font_big = get_font(38, bold=True)

    draw_human(draw, W // 2, 500, scale=1.0, expression="smug")

    t1 = "Can you beat"
    t2 = "frontier AI?"
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
        Scene(3.0,
              "Sixty second showdown. Human versus DeepSeek. Settler Rush.",
              scene_title),
        Scene(4.0,
              "Early game. Both players settle the coast. "
              "Score is tied at two each.",
              scene_early),
        Scene(5.0,
              "Mid game. DeepSeek starts trading aggressively. "
              "Three for one? It calls it fair. "
              "Then builds three roads in a single turn.",
              scene_mid),
        Scene(6.0,
              "Final turn. Both at nine points. One more to win. "
              "The human builds a settlement and takes it. Ten to nine.",
              scene_late),
        Scene(3.5,
              "Can you beat frontier AI? Find out at gghuman dot ai.",
              scene_cta),
    ]
    config = VideoConfig(
        scenes=scenes,
        output_path=f"{output_dir}/video3_60s_showdown.mp4",
        seed=777,
    )
    run_pipeline(config, engine)


if __name__ == "__main__":
    make_video()
