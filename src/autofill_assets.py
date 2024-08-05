# This script will contain code to generate textures.
import img_util as img_util
import util
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math

FONT_PATH = util.MDB_FOLDER_EDITING + "\\font\\dynamic01.otf"
GACHA_NAME_FONT_SIZE = 180
GACHA_NAME_MAX_WIDTH = 1450
GACHA_NAME_IMG_SIZE = (2048, 512)
GACHA_NAME_SHEER_FACTOR = 0.2
GACHA_NAME_COLORS = (
    (
        ((148,166,189),),
        ((170,199,218),)
    ),
    (
        ((189,138,8),),
        ((236,178,8),)
    ),
    (
        ((198,77,214),(181,89,214),(107,109,222),(33,142,222),(33,186,148),(57,207,82),(181,215,90)),
        ((227,75,238), (208,97,248),(126,129,255),(33,162,254),(31,220,169),(57,247,90),(202,247,41))
    ),
)


def generate_gacha_name_img(name: str, rarity: int=1):
    palette1 = GACHA_NAME_COLORS[rarity - 1][0]
    palette2 = GACHA_NAME_COLORS[rarity - 1][1]

    # First, determine the width of the text at default font size.
    print("Scaling font")
    font = ImageFont.truetype(FONT_PATH, GACHA_NAME_FONT_SIZE)
    text_bbox = font.getbbox(name)
    text_width = text_bbox[2] - text_bbox[0]

    # If the text is too wide, reduce the font size.
    if text_width > GACHA_NAME_MAX_WIDTH:
        font = ImageFont.truetype(FONT_PATH, math.floor(GACHA_NAME_FONT_SIZE * GACHA_NAME_MAX_WIDTH / text_width))
        text_bbox = font.getbbox(name)
        text_width = text_bbox[2] - text_bbox[0]

    # Draw the text.
    print("Draw text")
    text_layer = Image.new("RGBA", GACHA_NAME_IMG_SIZE, (255, 255, 255, 0))
    draw = ImageDraw.Draw(text_layer)
    midpoint = (GACHA_NAME_IMG_SIZE[0] / 2, GACHA_NAME_IMG_SIZE[1] / 2)
    anchor = 'mm'
    draw.text(midpoint, name, font=font, fill=(255, 255, 255, 255), anchor=anchor)

    # Squeeze the text vertically to 90% of the original height.
    print("Squeeze text")
    text_layer = text_layer.resize((GACHA_NAME_IMG_SIZE[0], math.floor(GACHA_NAME_IMG_SIZE[1] * 0.9)), Image.Resampling.BICUBIC)
    new_layer = Image.new("RGBA", GACHA_NAME_IMG_SIZE, (255, 255, 255, 0))
    new_layer.paste(text_layer, (0, math.floor(GACHA_NAME_IMG_SIZE[1] * 0.05)))
    new_new_layer = Image.new("RGB", GACHA_NAME_IMG_SIZE, (255, 255, 255))
    new_new_layer.putalpha(new_layer.split()[3])
    text_layer = new_new_layer

    # Apply horizontal sheering
    print("Sheer text")
    text_layer = text_layer.transform((text_layer.width, text_layer.height), Image.AFFINE, (1, GACHA_NAME_SHEER_FACTOR, -50, 0, 1, 0))
    text_layer = text_layer.filter(ImageFilter.GaussianBlur(1))


    # Create masks for the drop shadows.
    print("Create masks")
    mask1 = text_layer.copy().split()[3]
    mask2 = text_layer.copy().split()[3]

    # Mask 1 is the more opaque shadow.
    # Apply gaussian blur.
    # mask1 = mask1.filter(ImageFilter.GaussianBlur(2))
    mask2 = mask2.filter(ImageFilter.GaussianBlur(10))

    mask1 = mask1.point(lambda p: 255 if p > 0 else 0)
    mask2 = mask2.point(lambda p: 200 if p > 0 else 0)

    mask1 = mask1.filter(ImageFilter.GaussianBlur(4))
    mask2 = mask2.filter(ImageFilter.GaussianBlur(15))

    # Let's assume 100px is the maximum the shadow can spread.
    print("Create backgrounds")
    safezone = 70
    bg_bbox = (math.floor(midpoint[0] - text_bbox[2] / 2 - safezone), 0, math.ceil(midpoint[0] + text_bbox[2] / 2 + safezone), GACHA_NAME_IMG_SIZE[1])

    # Create backgrounds
    mask1_bg = Image.new("RGB", GACHA_NAME_IMG_SIZE, (0, 0, 0))
    mask1_bg_draw = ImageDraw.Draw(mask1_bg)
    mask2_bg = Image.new("RGB", GACHA_NAME_IMG_SIZE, (0, 0, 0))
    mask2_bg_draw = ImageDraw.Draw(mask2_bg)

    img_util.horz_gradient(mask1_bg_draw, img_util.Rect(*bg_bbox), img_util.gradient_color, palette1)
    img_util.horz_gradient(mask2_bg_draw, img_util.Rect(*bg_bbox), img_util.gradient_color, palette2)

    # Apply the alpha layers of the masks onto the backgrounds.
    mask1_bg.putalpha(mask1)
    mask2_bg.putalpha(mask2)

    # Debug: Save the layers.
    print("Save images")
    text_layer.save("text_layer.png")
    mask1_bg.save("mask1.png")
    mask2_bg.save("mask2.png")

    # Combine the layers.
    print("Combine images")
    tmp = Image.new("RGBA", GACHA_NAME_IMG_SIZE, (255, 255, 255, 0))
    tmp = Image.alpha_composite(tmp, mask2_bg)
    tmp = Image.alpha_composite(tmp, mask1_bg)
    tmp = Image.alpha_composite(tmp, text_layer)
    tmp.save("gacha_name.png")


def main():
    # generate_gacha_name_img("Special Week", 1)
    # generate_gacha_name_img("Special Week", 2)
    generate_gacha_name_img("Matikane Tannhäuser", 3)

if __name__ == "__main__":
    main()