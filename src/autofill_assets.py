# This script will contain code to generate textures.
import img_util as img_util
import util
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import glob
import json
import os
from tqdm import tqdm
from multiprocessing import Pool

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
    # print("Scaling font")
    font = ImageFont.truetype(FONT_PATH, GACHA_NAME_FONT_SIZE)
    text_bbox = font.getbbox(name)
    text_width = text_bbox[2] - text_bbox[0]

    # If the text is too wide, reduce the font size.
    if text_width > GACHA_NAME_MAX_WIDTH:
        font = ImageFont.truetype(FONT_PATH, math.floor(GACHA_NAME_FONT_SIZE * GACHA_NAME_MAX_WIDTH / text_width))
        text_bbox = font.getbbox(name)
        text_width = text_bbox[2] - text_bbox[0]

    # Draw the text.
    # print("Draw text")
    text_layer = Image.new("RGBA", GACHA_NAME_IMG_SIZE, (255, 255, 255, 0))
    draw = ImageDraw.Draw(text_layer)
    midpoint = (GACHA_NAME_IMG_SIZE[0] / 2, GACHA_NAME_IMG_SIZE[1] / 2)
    anchor = 'mm'
    draw.text(midpoint, name, font=font, fill=(255, 255, 255, 255), anchor=anchor)

    # Squeeze the text vertically to 90% of the original height.
    # print("Squeeze text")
    text_layer = text_layer.resize((GACHA_NAME_IMG_SIZE[0], math.floor(GACHA_NAME_IMG_SIZE[1] * 0.9)), Image.Resampling.BICUBIC)
    new_layer = Image.new("RGBA", GACHA_NAME_IMG_SIZE, (255, 255, 255, 0))
    new_layer.paste(text_layer, (0, math.floor(GACHA_NAME_IMG_SIZE[1] * 0.05)))
    new_new_layer = Image.new("RGB", GACHA_NAME_IMG_SIZE, (255, 255, 255))
    new_new_layer.putalpha(new_layer.split()[3])
    text_layer = new_new_layer

    # Apply horizontal sheering
    # print("Sheer text")
    text_layer = text_layer.transform((text_layer.width, text_layer.height), Image.AFFINE, (1, GACHA_NAME_SHEER_FACTOR, -50, 0, 1, 0))
    text_layer = text_layer.filter(ImageFilter.GaussianBlur(1))


    # Create masks for the drop shadows.
    # print("Create masks")
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
    # print("Create backgrounds")
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
    # print("Save images")
    # text_layer.save("text_layer.png")
    # mask1_bg.save("mask1.png")
    # mask2_bg.save("mask2.png")

    # Combine the layers.
    # print("Combine images")
    final = Image.new("RGBA", GACHA_NAME_IMG_SIZE, (255, 255, 255, 0))
    final = Image.alpha_composite(final, mask2_bg)
    final = Image.alpha_composite(final, mask1_bg)
    final = Image.alpha_composite(final, text_layer)
    
    return final


def fetch_gacha_name_data(type_folder: str, mdb_id: int):
    """Returns list of gacha names and rarities from the specified folder.
    Format: [(asset_path, name, rarity), ...]

    Args:
        type_folder (str): "charaname" or "supportname"
        mdb_id (int): The mdb id to fetch the names from.

    Returns:
        list: List of tuples - (asset_path, name, rarity)
    """
    out = []
    files = glob.glob(util.ASSETS_FOLDER_EDITING + f"\\gacha\\{type_folder}\\**\\*.json", recursive=True)
    for file in files:
        data = util.load_json(file)
        name_id, rarity = data['file_name'].rsplit("/", 1)[1].rsplit("_", 2)[1:]
        rarity = int(rarity)
        name_id = int(name_id)

        mdb_data = util.load_json(util.MDB_FOLDER_EDITING + f"\\text_data\\{mdb_id}.json")
        name = ""
        for entry in mdb_data:
            keys = json.loads(entry['keys'])
            if name_id == keys[0][-1]:
                name = entry['text']
                break
        
        if name == "":
            print(f"\nErr: Name not found for {file}")
            continue
        
        out.append((file, name, rarity))
    
    return out



def generate_gacha_name_images():
    # Index all gacha name images and generate them.
    # Fetch names from the correct mdb files.
    # Compare mdb name to name already in translation folder.
    # Only generate if different or not present.

    data = fetch_gacha_name_data("charaname", "170")
    data += fetch_gacha_name_data("supportname", "77")

    # Filter out names that don't need to be generated.
    names_path = util.ASSETS_FOLDER + "\\gacha\\names.json"
    existing_names = {}
    new_names = {}
    if os.path.exists(names_path):
        existing_names = util.load_json(names_path)
    
    # TODO: Remove this
    # existing_names = {}
    # data = data[:10]
    
    filtered_data = []
    for name_data in data:
        asset_path, name, rarity = name_data
        asset_basename = os.path.basename(asset_path).replace(".json", "")
        new_names[asset_basename] = name
        if asset_basename in existing_names and existing_names[asset_basename] == name:
            continue
        filtered_data.append(name_data)
    
    # Generate the images.
    with Pool() as pool:
        list(tqdm(pool.imap_unordered(pool_generate_gacha_name_image, filtered_data, chunksize=16), total=len(filtered_data), desc="Generating images"))


    # for name_data in filtered_data:
    #     pool_generate_gacha_name_image(name_data)
    
    # Save the names to the names.json file.
    os.makedirs(os.path.dirname(names_path), exist_ok=True)
    util.save_json(names_path, new_names)

def pool_generate_gacha_name_image(name_data):
    asset_path, name, rarity = name_data
    # print(f"\nGenerating image for {name} - {rarity}")
    img = generate_gacha_name_img(name, rarity)
    img.save(asset_path.replace(".json", ".png"))


def main():
    # generate_gacha_name_img("Special Week", 1)
    # generate_gacha_name_img("Special Week", 2)
    # generate_gacha_name_img("Matikane Tannhäuser", 3)

    generate_gacha_name_images()

if __name__ == "__main__":
    main()