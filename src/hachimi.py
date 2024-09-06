import util
import os
import re
import shutil
import glob
import unity
from UnityPy.enums import ClassIDType
import fnv
from PIL import Image
from tqdm import tqdm
from multiprocessing import Pool

HACHIMI_ROOT = "tl-en\\localized_data\\"

def convert_tags(text: str) -> str:
    if "<p=" in text:
        return ""
    text =  text.replace("<nb>", "$(nb)")\
                .replace("<force>", "")\
                .replace("<ho>", "$(ho 1)")\
                .replace("<vo>", "$(vo 1)")\
                .replace("<nho>", "$(ho 0)")\
                .replace("<nvo>", "$(vo 0)")\
                .replace("<rbr>", "")\
                .replace("<br>", "")\
                .replace("<fit>", "")\
                .replace("<mon>10", "$(month 10)")\
                .replace("<mon>11", "$(month 11)")\
                .replace("<mon>12", "$(month 12)")\
                .replace("<mon>1", "$(month 1)")\
                .replace("<mon>2", "$(month 2)")\
                .replace("<mon>3", "$(month 3)")\
                .replace("<mon>4", "$(month 4)")\
                .replace("<mon>5", "$(month 5)")\
                .replace("<mon>6", "$(month 6)")\
                .replace("<mon>7", "$(month 7)")\
                .replace("<mon>8", "$(month 8)")\
                .replace("<mon>9", "$(month 9)")\
                .replace("<mon>{0}", "$(month {0})")\
                .replace("<mon>{1}", "$(month {1})")\
                .replace("{0}<ord={0}>", "$(ordinal {0})")\
                .replace("{1}<ord={1}>", "$(ordinal {1})")

    regex = re.compile(r"<sc=(\d+)>")
    text = regex.sub(r"$(scale \1)", text)

    regex = re.compile(r"<a(\d+)>")
    text = regex.sub(r"$(anchor \1)", text)

    return text


def convert_jpdict():
    print("JPDict")
    jpdict_path = util.ASSEMBLY_FOLDER + "jpdict.json"
    jpdict = util.load_json(jpdict_path)
    in_dict = {}
    for key, entry in jpdict.items():
        text = convert_tags(entry.get("processed", entry["text"]))
        if not text:
            continue
        in_dict[key] = text

    out_path = os.path.join(HACHIMI_ROOT, "localize_dict.json")
    out_dict = {}
    if os.path.exists(out_path):
        out_dict = util.load_json(out_path)
    out_dict.update(in_dict)

    dict_keys = [key for key in out_dict.keys()]
    dict_keys.sort()
    out_dict = {key: out_dict[key] for key in dict_keys}

    util.save_json(out_path, out_dict)


def convert_hashed():
    print("Hashed")
    # Do this with editing version? Need to rehash
    hashed_path = util.ASSEMBLY_FOLDER_EDITING + "hashed.json"
    hashed_list = util.load_json(hashed_path)
    in_dict = {}
    for entry in hashed_list:
        text = convert_tags(entry.get("processed", entry["text"]))
        if not text:
            continue
        if not "source" in entry:
            continue
        hash_int = fnv.fnv1a_64(entry["source"].encode('utf_16_le'))
        in_dict[str(hash_int)] = text
    
    out_path = os.path.join(HACHIMI_ROOT, "hashed_dict.json")
    out_dict = {}
    if os.path.exists(out_path):
        out_dict = util.load_json(out_path)

    out_dict.update(in_dict)

    dict_keys = [int(key) for key in out_dict.keys()]
    dict_keys.sort()
    out_dict = {str(key): out_dict[str(key)] for key in dict_keys}
    

    util.save_json(out_path, out_dict)


def convert_assembly():
    print("==Assembly==")
    convert_jpdict()
    convert_hashed()


def convert_mdb_nested(json_folder: str, out_path: str):
    new_dict = {}

    data_path = json_folder
    jsons = glob.glob(data_path + "/*.json")

    for json_path in jsons:
        category = os.path.basename(json_path).replace(".json", "")
        new_dict[category] = {}

        data = util.load_json(json_path)

        for key, entry in data.items():
            text = convert_tags(entry["text"])
            if not text:
                continue
            new_dict[category][key] = text
    
    out_dict = {}
    if os.path.exists(out_path):
        out_dict = util.load_json(out_path)

    for category, entries in new_dict.items():
        if category not in out_dict:
            out_dict[category] = {}
        out_dict[category].update(entries)
    
    # Sort out_dict by integer category keys
    dict_keys = [int(key) for key in out_dict.keys()]
    dict_keys.sort()
    out_dict = {str(key): out_dict[str(key)] for key in dict_keys}
    
    util.save_json(out_path, out_dict)


def convert_mdb_single(json_path: str, out_path: str):
    new_dict = {}
    data_path = json_path

    if not os.path.exists(data_path):
        print(f"File {data_path} does not exist")
        return

    data = util.load_json(data_path)

    for key, entry in data.items():
        text = convert_tags(entry["text"])
        if not text:
            continue
        new_dict[key] = text
    
    out_dict = {}
    if os.path.exists(out_path):
        out_dict = util.load_json(out_path)

    out_dict.update(new_dict)

    dict_keys = [int(key) for key in out_dict.keys()]
    dict_keys.sort()
    out_dict = {str(key): out_dict[str(key)] for key in dict_keys}

    util.save_json(out_path, out_dict)


def convert_text_data():
    print("text_data")
    convert_mdb_nested(os.path.join(util.MDB_FOLDER, "text_data"), os.path.join(HACHIMI_ROOT, "text_data_dict.json"))


def convert_character_system_text():
    print("character_system_text")
    convert_mdb_nested(os.path.join(util.MDB_FOLDER, "character_system_text"), os.path.join(HACHIMI_ROOT, "character_system_text_dict.json"))


def convert_race_jikkyo():
    print("jikkyo")
    
    # TODO: Remove wrap because it should be handled by Hachimi.
    convert_mdb_single(os.path.join(util.MDB_FOLDER, "race_jikkyo_message.json"), os.path.join(HACHIMI_ROOT, "race_jikkyo_message_dict.json"))
    convert_mdb_single(os.path.join(util.MDB_FOLDER, "race_jikkyo_comment.json"), os.path.join(HACHIMI_ROOT, "race_jikkyo_comment_dict.json"))


def convert_mdb():
    print("==MDB==")
    convert_text_data()
    convert_character_system_text()
    convert_race_jikkyo()


def make_png_diff(new_path: str, out_path: str) -> bool:
    source_path = new_path.replace(".png", ".org.png")

    
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source path {source_path} does not exist")
    
    if not os.path.exists(new_path):
        raise FileNotFoundError(f"New path {new_path} does not exist")
    
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Crude way to skip unchanged files
    if os.path.exists(out_path):
        diff_time = os.path.getmtime(out_path)
        new_time = os.path.getmtime(new_path)

        # If the new file was not modified after the diff file was generated, skip
        if diff_time > new_time:
            return False

    old_img = Image.open(source_path)
    new_img = Image.open(new_path)
    width = old_img.width
    height = old_img.height
    if width != new_img.width or height != new_img.height:
        print("[Error] Image size mismatch")

    old_pixels = old_img.load()
    new_pixels = new_img.load()

    out_img = Image.new("RGBA", (width, height), None)
    out_pixels = out_img.load()
    for x in range(width):
        for y in range(height):
            old_pixel = old_pixels[x,y]
            new_pixel = new_pixels[x,y]
            if old_pixel != new_pixel:
                if new_pixel[3] == 0 and old_pixel[3] != 0:
                    new_pixel = (255, 0, 255, 255)
                elif new_pixel == (255, 0, 255, 255):
                    new_pixel = (255, 0, 255, 254)
                out_pixels[x,y] = new_pixel

    out_img.save(out_path, "PNG", compress_level=9)

    return True


def convert_flash(flash_metadata: list):
    print("Flash")

    for meta in flash_metadata:
        meta = meta[0]

        bundle_path = util.get_asset_path(meta['hash'])
        if not os.path.exists(bundle_path): 
            print(f"Assetbundle {bundle_path} does not exist")
            continue

        asset, root = unity.load_assetbundle(bundle_path, meta['hash'])

        motion_parameter_list = []

        for obj in asset.objects:
            tree = obj.read_typetree()
            if not tree.get("_motionParameterGroup"):
                continue
            
            motion_parameter_list = tree['_motionParameterGroup'].get('_motionParameterList')
            break
        
        if not motion_parameter_list:
            print(f"No motion parameter list found in {meta['file_name']}")
            continue

        out_params = {}

        for params_dict in meta['data'].values():
            for param_id, param_data in params_dict.items():
                param_idx = [param_dict['_id'] for param_dict in motion_parameter_list].index(param_id)
                for txt_param_name, txt_param_data in param_data.items():
                    txt_param_idx = [param_dict['_objectName'] for param_dict in motion_parameter_list[param_idx]['_textParamList']].index(txt_param_name)

                    entry = {}
                    if '_text' in txt_param_data:
                        entry['text'] = txt_param_data['_text']
                    if '_positionOffset' in txt_param_data:
                        entry['position_offset'] = txt_param_data['_positionOffset']
                    if '_scale' in txt_param_data:
                        entry['scale'] = txt_param_data['_scale']

                    if not param_idx in out_params:
                        out_params[param_idx] = {"text_param_list": {}}
                    
                    if not txt_param_idx in out_params[param_idx]["text_param_list"]:
                        out_params[param_idx]["text_param_list"][txt_param_idx] = {}
                    
                    out_params[param_idx]["text_param_list"][txt_param_idx] = entry
        
        out_params = {
            "windows": {"bundle_name": meta['hash']},
            "data": {"motion_parameter_list": out_params}
            }

        out_path = os.path.join(HACHIMI_ROOT, "assets", meta['file_name'] + ".json")
        out_json = {}

        if os.path.exists(out_path):
            out_json = util.load_json(out_path)
        
        out_json.update(out_params)

        util.save_json(out_path, out_json)


def get_atlas_bundle_hash(file_name: str) -> str:
    new_name = file_name[:-4]
    with util.MetaConnection() as (conn, cursor):
        cursor.execute("SELECT h FROM a WHERE n = ?", (new_name,))
        row = cursor.fetchone()
        return row[0]


def convert_texture_atlas(meta: dict):
    folder = os.path.join(util.ASSETS_FOLDER_EDITING, meta['file_name'])

    if len(meta['textures']) > 1:
        # There should not be more, otherwise things will break in Hachimi.
        print(f"More than 1 texture in {meta['file_name']}!!")
    
    for texture in meta['textures']:
        png_path = os.path.join(folder, texture['name'] + ".png")
        if not os.path.exists(png_path):
            print(f"File {png_path} does not exist")
            return

        # There should only be 1 texture here! If there are more, it will be overwritten!
        atlas_name = meta['file_name'].split("/")[1]
        out_file = os.path.join(HACHIMI_ROOT, "assets", "atlas", atlas_name, atlas_name + ".diff.png")
        out_folder = os.path.dirname(out_file)
        os.makedirs(out_folder, exist_ok=True)


        replaced = make_png_diff(png_path, out_file)
        if not replaced:
            return
        # shutil.copy(png_path, out_file)

        out_json_path = out_file[:-9] + ".json"
        new_json = {
            "windows": {"bundle_name": get_atlas_bundle_hash(meta['file_name'])}
        }
        out_json = {}

        if os.path.exists(out_json_path):
            out_json = util.load_json(out_json_path)

        out_json.update(new_json)
        util.save_json(out_json_path, out_json)


def convert_texture_flash(meta: dict):
    folder = os.path.join(util.ASSETS_FOLDER_EDITING, meta['file_name'])

    bundle_path = util.get_asset_path(meta['hash'])
    if not os.path.exists(bundle_path):
        print(f"Assetbundle {bundle_path} does not exist")
        return

    asset, root = unity.load_assetbundle(bundle_path, meta['hash'])

    meshparam_group_list = []
    textures = {}
    meshparam_name = ""

    for obj in asset.objects:
        if obj.type == ClassIDType.Texture2D:
            textures[obj.path_id] = obj

        tree = obj.read_typetree()
        if tree.get('m_Name', "").startswith("as_uMeshParam_"):
            meshparam_name = tree['m_Name']
            meshparam_group_list += tree['_meshParameterGroupList']
    
    if not meshparam_group_list:
        convert_texture_texture2d(meta)
        return

    for meshparam_group in meshparam_group_list:
        path_id = meshparam_group.get("_textureSetColor", {}).get("m_PathID")
        if not path_id or path_id not in textures:
            continue

        texture = textures.get(path_id)
        texture_name = meshparam_group['_textureSetName']
        tree = texture.read_typetree()

        texture_file = tree.get("m_Name")

        texture_path = os.path.join(folder, texture_file + ".png")

        if not os.path.exists(texture_path):
            print(f"File {texture_path} does not exist. Source: {meta['file_name']}")
            continue

        out_path = os.path.join(HACHIMI_ROOT, "assets", "an_texture_sets", meshparam_name, texture_name + ".diff.png")
        out_folder = os.path.dirname(out_path)
        os.makedirs(out_folder, exist_ok=True)

        make_png_diff(texture_path, out_path)
        # shutil.copy(texture_path, out_path)


def convert_texture_texture2d(meta: dict):
    folder = os.path.join(util.ASSETS_FOLDER_EDITING, meta['file_name'])

    if len(meta['textures']) > 1:
        # There should not be more, otherwise things will break in Hachimi.
        print(f"More than 1 texture in {meta['file_name']}!!")

    for texture in meta['textures']:
        png_path = os.path.join(folder, texture['name'] + ".png")
        if not os.path.exists(png_path):
            print(f"File {png_path} does not exist")
            continue

        # There should only be 1 texture here! If there are more, it will be overwritten!
        out_file = os.path.join(HACHIMI_ROOT, "assets", "textures", meta['file_name'] + ".diff.png")
        out_folder = os.path.dirname(out_file)
        os.makedirs(out_folder, exist_ok=True)

        make_png_diff(png_path, out_file)
        # shutil.copy(png_path, out_file)

def _convert_texture(meta):
    meta = meta[0]

    folder = os.path.join(util.ASSETS_FOLDER_EDITING, meta['file_name'])
    if not os.path.exists(folder):
        print(f"Folder {folder} does not exist")
        return

    if meta['file_name'].startswith("atlas/"):
        # Atlas
        convert_texture_atlas(meta)

    elif meta['file_name'].startswith(("uianimation/flash/", "sourceresources/flash/")):
        # Flash
        convert_texture_flash(meta)
    else:
        # Texture2D
        convert_texture_texture2d(meta)

def convert_textures(texture_metadata: list):
    print("Textures")

    with Pool() as p:
        list(tqdm(p.imap_unordered(_convert_texture, texture_metadata, chunksize=16), total=len(texture_metadata)))
    
    # for meta in texture_metadata:
    #     _convert_texture(meta)


def convert_stories(story_data: list):
    print("Stories")
    for data in story_data:
        data = data[0]

        out_path = os.path.join(HACHIMI_ROOT, "assets", data['file_name'] + ".json")
        out_block_list = []

        for block in data['data']:
            if not out_block_list and not block.get('text'):
                continue

            block_dict = {}

            block_dict['text'] = block.get('text', "")

            name = block.get('name')
            if name:
                block_dict['name'] = name
            
            choices = block.get('choices')
            if choices:
                block_dict['choice_data_list'] = [convert_tags(choice.get('processed', choice.get('text', ""))) for choice in choices]
            
            out_block_list.append(block_dict)
        
        out_dict = {"text_block_list": out_block_list}
        util.save_json(out_path, out_dict)


def convert_movies(movie_metadata: list):
    print("Movies")
    for meta in movie_metadata:
        meta = meta[0]

        file_name = meta['file_name']

        local_file = os.path.join(util.ASSETS_FOLDER_EDITING, file_name)
        hachimi_file = os.path.join(HACHIMI_ROOT, "assets", "movies", file_name.replace("movie/m/", ""))

        if not os.path.exists(local_file):
            print(f"Movie {local_file} does not exist")
            continue

        os.makedirs(os.path.dirname(hachimi_file), exist_ok=True)
        shutil.copy(local_file, hachimi_file)


def convert_assets():
    print("==Assets==")
    asset_dict = util.get_assets_type_dict()
    convert_flash(asset_dict.get('flash', []))
    convert_textures(asset_dict.get('texture', []))
    convert_stories(asset_dict.get('story', []))
    convert_movies(asset_dict.get('movie', []))


def copy_data():
    print("==Copying data==")
    from_folder = HACHIMI_ROOT
    to_folder = os.path.join(util.get_game_folder(), "hachimi", "localized_data")

    shutil.copytree(from_folder, to_folder, dirs_exist_ok=True)


def convert():
    print("Starting conversion to Hachimi")
    convert_assembly()
    convert_mdb()
    convert_assets()

    copy_data()
    print("Done")


def main():
    # convert()
    convert_assembly()
    convert_mdb()
    copy_data()

if __name__ == "__main__":
    main()
