import os
import util
import hashlib
import unity
import tqdm
import time
from multiprocessing import Pool
from pathvalidate import sanitize_filename
import glob
import version
import intermediate
import json
import shutil
from itertools import repeat
import UnityPy
import _import

def add_to_dict(parent_dict, values_list):
    if len(values_list) == 2:
        parent_dict[str(values_list[0])] = {"text": "", "hash": hashlib.sha256(str(values_list[1]).encode("utf-8")).hexdigest()}
    else:
        if values_list[0] not in parent_dict:
            parent_dict[values_list[0]] = {}
        add_to_dict(parent_dict[values_list[0]], values_list[1:])

def index_table(table, keys):
    with util.MDBConnection() as (_, cursor):
        cursor.execute(
            f"""SELECT {','.join(keys)} FROM {table}"""
        )
        rows = cursor.fetchall()
    
    if not rows:
        raise ValueError(f"No rows found for table {table} with keys {keys}")
    
    data_dict = {}
    
    for row in rows:
        add_to_dict(data_dict, row)

    intermediate.write_recursive(os.path.join("tmp", table), data_dict)


def index_mdb():
    print("=== EXTRACTING MDB ===")
    index = util.load_json("src/index.json")

    for table, keys in index.items():
        print(table)
        index_table(table, keys)
    
    intermediate.mdb_to_intermediate(tmp_path="tmp")
    print("Done")


def create_write_path(file_name):
    path, name = file_name.rsplit("/", 1)

    if file_name.startswith("story/"):
        path = path.replace("/data/", "/")
        return os.path.join(
            util.ASSETS_FOLDER_EDITING,
            path,
            name[-3:] + ".json")

    elif file_name.startswith("home/"):
        path = path.replace("/data/", "/")
        return os.path.join(
            util.ASSETS_FOLDER_EDITING,
            path,
            name[-7:-3],
            name[-3:] + ".json")

    elif file_name.startswith("race/"):
        path = path.replace("/storyrace/text", "/")
        return os.path.join(
            util.ASSETS_FOLDER_EDITING,
            path,
            name[-9:-7],
            name[-7:-3],
            name[-3:] + ".json"
        )

    else:
        raise NotImplementedError(f"Unknown asset type for {file_name}")


def load_asset_data(row_metadata):
    row_data = row_metadata['row_data']
    new = row_metadata['new']
    # Load the story data from the unity asset bundle.
    row_index = row_data[0]
    file_name = row_data[1]
    hash = row_data[2]

    file_path = os.path.join(util.DATA_PATH, hash[:2], hash)

    if not os.path.exists(file_path):
        print(f"\nUser has not downloaded story data {file_name} ({hash}) or the hash has changed. Skipping.")
        return

    root = unity.load_assetbundle(file_path)

    if not root:
        return

    tree = root.read_typetree()

    tl_item = {
        "type": "story",
        "version": version.VERSION,
        "row_index": row_index,
        "file_name": file_name,
        "hash": hash,
        "data": []
    }

    if file_name.startswith("race/"):
        for text in tree['textData']:
            clip_item = {
                "text": "",
                "source": text['text'],
            }
            tl_item["data"].append(clip_item)

    else:
        tl_item['title'] = tree['Title']
        # Story blocks
        for block in tree['BlockList']:
            for clip in block['TextTrack']['ClipList']:
                path_id = clip['m_PathID']
                text_asset = root.assets_file.files[path_id]
                text_data = text_asset.read_typetree()

                source_text = text_data['Text']
                source_name = text_data['Name']

                clip_item = {
                    "path_id": path_id,
                    "block_id": block['BlockIndex'],
                    "text": "",
                    "source": source_text,
                    # "source_hash": hashlib.sha256(str(source_text).encode("utf-8")).hexdigest(),
                    "name": "",
                    "source_name": source_name,
                    # "source_name_hash": hashlib.sha256(str(source_name).encode("utf-8")).hexdigest()
                }

                if text_data.get("ClipLength"):
                    clip_item["clip_length"] = text_data["ClipLength"]
                    clip_item["source_clip_length"] = text_data["ClipLength"]

                    for track_group in block['CharacterTrackList']:
                        for key in track_group.keys():
                            if key.endswith("MotionTrackData") and track_group[key]['ClipList']:
                                if 'anim_data' not in clip_item:
                                    clip_item['anim_data'] = []
                                clip_path_id = track_group[key]['ClipList'][-1]['m_PathID']
                                anim_asset = root.assets_file.files[clip_path_id]
                                if anim_asset:
                                    anim_data = anim_asset.read_typetree()
                                    anim_group_data = {}
                                    anim_group_data['orig_length'] = anim_data['ClipLength']
                                    anim_group_data['path_id'] = clip_path_id
                                    clip_item['anim_data'].append(anim_group_data)

                if text_data.get('ChoiceDataList'):
                    clip_item["choices"] = []
                    for choice in text_data['ChoiceDataList']:
                        choice_item = {
                            "text": "",
                            "source": choice['Text'],
                            # "source_hash": hashlib.sha256(str(choice['Text']).encode("utf-8")).hexdigest(),
                        }
                        clip_item["choices"].append(choice_item)
                
                if text_data.get('ColorTextInfoList'):
                    clip_item["color_info"] = []
                    for color_info in text_data['ColorTextInfoList']:
                        color_item = {
                            "text": "",
                            "source": color_info['Text'],
                            # "source_hash": hashlib.sha256(str(color_info['Text']).encode("utf-8")).hexdigest(),
                        }
                        clip_item["color_info"].append(color_item)

                tl_item["data"].append(clip_item)

    write_path = create_write_path(tl_item['file_name'])

    os.makedirs(os.path.dirname(write_path), exist_ok=True)

    if not new:
        print(f"\nStory data {tl_item['file_name']} has changed. Creating backup and replacing.", flush=True)
        os.rename(write_path, write_path + f".{round(time.time())}")

    with open(write_path, "w", encoding="utf-8") as f:
        f.write(util.json.dumps(tl_item, indent=4, ensure_ascii=False))

    return

def check_existing_hash(row_data):
    file_name = row_data[1]
    hash = row_data[2]

    check_path = create_write_path(file_name)

    existing_files = glob.glob(check_path)

    output = {
        "row_data": row_data,
        "update": True,
        "new": True
    }

    if existing_files:
        # For some reason this does not cause any time difference.
        # The act of opening the file is probably the bottleneck.
        existing_data = util.load_json(existing_files[0])
        if existing_data["hash"] == hash:
            output["update"] = False
        else:
            output["new"] = False

        # existing_hash = None
        # with open(existing_files[0], "r", encoding="utf-8") as f:
        #     for line in f:
        #         line = line.strip()
        #         if line.startswith('"hash":'):
        #             existing_hash = line.split('"')[3]
        #             break
        # if existing_hash == hash:
        #     output["update"] = False
        # else:
        #     output["new"] = False
    
    return output

def update_story_intermediate(path_to_existing):
    base_path = path_to_existing[len(util.ASSETS_FOLDER):]
    intermediate_path = os.path.join(util.ASSETS_FOLDER_EDITING, base_path)

    existing_data = util.load_json(path_to_existing)

    if not os.path.exists(intermediate_path):
        # Translation exists but no intermediate file. Create one.
        load_asset_data({
            "new": True,
            "row_data": [
                existing_data['row_index'],
                existing_data['file_name'],
                existing_data['hash']
            ]
        })

    if not os.path.exists(intermediate_path):
        # A new intermediate file was not created. The hash must have changed.
        # We no longer know what was in the original file, so backup the existing file instead.
        print(f"\nStory data {base_path} with hash ({existing_data['hash']}) no longer exists. Creating backup using translation file.", flush=True)
        shutil.copy(path_to_existing, intermediate_path + f".{round(time.time())}")
        return

    try:
        intermediate_data = util.load_json(intermediate_path)
    except json.JSONDecodeError:
        print(f"\nError loading {intermediate_path}. Moving to backup.")
        os.rename(intermediate_path, intermediate_path + f".{round(time.time())}")
        return

    if existing_data['hash'] != intermediate_data['hash']:
        return
    for i, line in enumerate(existing_data['data']):
        if existing_data['file_name'].startswith("race/"):
            intermediate_data['data'][i]['text'] = line
            continue

        if line['text'] or line['name']:
            for key, value in line.items():
                intermediate_data['data'][i][key] = value
    with open(intermediate_path, "w", encoding="utf-8") as f:
        f.write(util.json.dumps(intermediate_data, indent=4, ensure_ascii=False))

def index_story(debug=False):
    print("=== EXPORTING STORY ===")
    with Pool() as pool:
        # First, apply all current translations to any existing intermediate files.
        existing_jsons = []
        existing_jsons += glob.glob(util.ASSETS_FOLDER + "story/**/*.json", recursive=True)
        existing_jsons += glob.glob(util.ASSETS_FOLDER + "home/**/*.json", recursive=True)
        existing_jsons += glob.glob(util.ASSETS_FOLDER + "race/**/*.json", recursive=True)

        # for i, path in enumerate(existing_jsons):
        #     if i % 100 == 0:
        #         print(f"{i+1}/{len(existing_jsons)}")
        #     update_story_intermediate(path)

        print("Updating local files from existing translations")
        _ = list(tqdm.tqdm(pool.imap_unordered(update_story_intermediate, existing_jsons, chunksize=128), total=len(existing_jsons)))

        # Find all stories in the meta DB.
        with util.MetaConnection() as (_, cursor):
            cursor.execute(
                """SELECT i, n, h FROM a WHERE
                n like 'story/data/__/____/storytimeline%'
                OR n like 'home/data/_____/__/hometimeline%'
                OR n like 'race/storyrace/text/%'
                ORDER BY n ASC;"""
            )
            rows = cursor.fetchall()

        if not rows:
            raise ValueError("No story data found in meta DB.")

        print(f"Found {len(rows)} story data entries.")

        # # For testing purposes
        # rows = rows[:1]


        print("Checking if local files need to be extracted")
        print(len(rows))

        rows_to_update = list(tqdm.tqdm(pool.imap_unordered(check_existing_hash, rows, chunksize=256), total=len(rows)))

        rows_to_update = [row for row in rows_to_update if row['update']]

        print("Extracting files")
        print(len(rows_to_update))

        if debug:
            for row in rows_to_update:
                load_asset_data(row)
        else:
            _ = list(tqdm.tqdm(pool.imap_unordered(load_asset_data, rows_to_update, chunksize=64), total=len(rows_to_update)))


def index_one_lyric(metadata):
    row_index = metadata[0]
    file_name = metadata[1]
    hash = metadata[2]

    file_path = os.path.join(util.DATA_PATH, hash[:2], hash)

    if not os.path.exists(file_path):
        print(f"\nUser has not downloaded lyrics {file_name}. Skipping.")
        return

    write_path = os.path.join(util.ASSETS_FOLDER_EDITING, "lyrics", file_name.split("/")[2][1:] + ".json")
    tl_path = os.path.join(util.ASSETS_FOLDER, "lyrics", file_name.split("/")[2][1:] + ".json")
    os.makedirs(os.path.dirname(write_path), exist_ok=True)
    
    root = unity.load_assetbundle(file_path)

    if not root:
        return


    tree = root.read_typetree()

    script = [line.strip() for line in tree['m_Script'].split("\n") if line.strip()]

    cached_intermediates = []

    if os.path.exists(write_path):
        with open(write_path, "r", encoding="utf-8") as f:
            cached_intermediates = util.json.load(f)['data']
    
    cached_translations = []
    if os.path.exists(tl_path):
        with open(tl_path, "r", encoding="utf-8") as f:
            cached_translations = util.json.load(f)['data']

    lyric_list = []

    for index, line in enumerate(script[1:]):
        line_split = line.split(",", 1)
        tl_item = {
            "text": "",
            "prev_text": "",
            "source": line_split[1],
            "hash": hashlib.sha256(str(line_split[1]).encode("utf-8")).hexdigest(),
            "changed": False
        }

        if cached_intermediates:
            cached_item = cached_intermediates[index]
            if cached_item['text']:
                tl_item['prev_text'] = cached_item['text']
                
                if cached_item['hash'] != tl_item['hash']:
                    tl_item['changed'] = True
                else:
                    tl_item['text'] = cached_item['text']

        if cached_translations:
            cached_item = cached_translations[index]
            if cached_item['text']:
                if cached_item['hash'] != tl_item['hash']:
                    tl_item['changed'] = True
                else:
                    tl_item['text'] = cached_item['text']

        lyric_list.append(tl_item)

    tl_file = {
        "type": "lyrics",
        "version": version.VERSION,
        "row_index": row_index,
        "file_name": file_name,
        "hash": hash,
        "data": lyric_list
    }

    with open(write_path, "w", encoding="utf-8") as f:
        f.write(util.json.dumps(tl_file, indent=4, ensure_ascii=False))


def index_lyrics():
    print("=== EXTRACTING LYRICS ===")
    with util.MetaConnection() as (_, cursor):
        cursor.execute(
            """SELECT i, n, h FROM a WHERE n like 'live/%lyrics' ORDER BY n ASC;"""
        )
        rows = cursor.fetchall()
    
    if not rows:
        raise ValueError("No lyrics found in meta DB.")
    
    for metadata in rows:
        index_one_lyric(metadata)


def index_textures_from_assetbundle(metadata):
    file_name = metadata[0]
    hash = metadata[1]

    file_path = os.path.join(util.DATA_PATH, hash[:2], hash)

    if not os.path.exists(file_path):
        print(f"\nUser has not downloaded atlas {file_name}. Skipping.")
        return
    
    meta_file_path = os.path.join(util.ASSETS_FOLDER_EDITING, file_name, os.path.basename(file_name) + ".json")

    if os.path.exists(meta_file_path):
        existing_meta = util.load_json(meta_file_path)
        if existing_meta['hash'] == hash:
            # Already indexed and no change in hash.
            if not 'new' in existing_meta:
                existing_meta['new'] = True
            if existing_meta['new']:
                existing_meta['new'] = False
                with open(meta_file_path, "w", encoding='utf-8') as f:
                    f.write(json.dumps(existing_meta, indent=4, ensure_ascii=False))
            return
        else:
            # Hash has changed. Create a backup.
            print(f"\nTexture atlas {file_name} has changed. Creating backup and replacing.", flush=True)
            for texture in existing_meta['textures']:
                backup_texture(file_name, texture)
    
    try:
        root = unity.load_assetbundle(file_path)
    except:
        print(f"\nError loading texture {file_name}. Skipping.")
        return

    # TODO: Split every texture into its sprites, save them individually.
    # Combine them back when creating diff file later.

    textures_list = []

    for asset in root.assets_file.objects.values():
        # If Texture2D, extract the image.
        if asset.type.name == "Texture2D":
            image = asset.read()

            name = image.name
            path_id = asset.path_id

            textures_list.append({
                "name": name,
                "path_id": path_id
            })

            dest = os.path.join(util.ASSETS_FOLDER_EDITING, file_name, image.name)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            image.image.save(dest + ".org.png")
            if not os.path.exists(dest + ".png"):
                shutil.copy(dest + ".org.png", dest + ".png")

    if textures_list:
        with open(meta_file_path, "w", encoding='utf-8') as f:
            f.write(json.dumps(
                {
                    "type": "texture",
                    "version": version.VERSION,
                    "file_name": file_name,
                    "hash": hash,
                    "new": True,
                    "textures": textures_list,
                }, indent=4, ensure_ascii=False
            ))

def backup_texture(file_name, texture):
    texture_path = os.path.join(util.ASSETS_FOLDER_EDITING, file_name, texture['name'] + ".png")
    org_path = texture_path[:-4] + ".org.png"
    for path in [texture_path, org_path]:
        if os.path.exists(path):
            shutil.move(path, path[:-4] + f".{round(time.time())}.png")


def process_existing_texture(metadata):
    hash = metadata['hash']
    file_name = metadata['file_name']
    meta_file_path = os.path.join(util.ASSETS_FOLDER_EDITING, file_name, os.path.basename(file_name) + ".json")
    if not os.path.exists(meta_file_path):
        # This is a new texture. Create a new intermediate file.
        out_folder = os.path.join(util.ASSETS_FOLDER_EDITING, file_name)
        os.makedirs(out_folder, exist_ok=True)
        png_out = os.path.join(out_folder, os.path.basename(file_name) + ".png")
        org_out = os.path.join(out_folder, os.path.basename(file_name) + ".org.png")
        hash_out = os.path.join(out_folder, os.path.basename(file_name) + ".hash")
        asset_bundle = UnityPy.load(util.get_asset_path(hash))
        for texture in metadata['textures']:
            path_id = texture['path_id']
            diff_path = os.path.join(util.ASSETS_FOLDER, file_name, texture['name'] + ".diff")
            new_bytes, texture_read = _import.create_new_image_from_path_id(asset_bundle, path_id, diff_path)
            texture_read.image.save(org_out)
            with open(png_out, "wb") as f:
                f.write(new_bytes)
            
            hasher = hashlib.sha256()
            hasher.update(new_bytes)
            with open(hash_out, "wb") as f:
                f.write(hasher.digest())
        
        # Create meta file
        meta_data = {
            "type": "texture",
            "version": version.VERSION,
            "file_name": file_name,
            "hash": hash,
            "new": False,
            "textures": metadata['textures'],
        }

        with open(meta_file_path, "w", encoding='utf-8') as f:
            f.write(json.dumps(meta_data, indent=4, ensure_ascii=False))

    else:
        # This is an existing texture. Check if the hash has changed.
        existing_meta = util.load_json(meta_file_path)
        if existing_meta['hash'] == hash:
            return
        # The hash has changed. Create a backup.
        print(f"\nTexture {file_name} has changed. Creating backup and replacing.", flush=True)
        for texture in existing_meta['textures']:
            backup_texture(file_name, texture)

def index_textures():
    """Index all texture atlases.
    """
    print("=== EXTRACTING TEXTURES ===")

    # First, turn already translated textures into intermediate
    existing_jsons = []
    existing_jsons += glob.glob(util.ASSETS_FOLDER + "/**/*.json", recursive=True)

    with Pool() as pool:
        results = list(tqdm.tqdm(pool.imap_unordered(util.test_for_type, zip(existing_jsons, repeat("texture"))), total=len(existing_jsons), desc="Looking for translated textures"))

        results = [result[1] for result in results if result[0]]

        _ = list(tqdm.tqdm(pool.imap_unordered(process_existing_texture, results), total=len(results), desc="Processing existing textures"))

    all_textures = []

    with util.MetaConnection() as (_, cursor):
        cursor.execute(
            """SELECT n, h FROM a WHERE n like 'atlas/%_tex' ORDER BY n ASC;"""
        )
        rows = cursor.fetchall()
        all_textures += rows

        cursor.execute(
            """SELECT n, h FROM a WHERE n like 'uianimation/flash/%' ORDER BY n ASC;"""
        )
        rows = cursor.fetchall()
        all_textures += rows

        cursor.execute(
            """SELECT n, h FROM a WHERE n like 'home/ui/texture/%' ORDER BY n ASC;"""
        )
        rows = cursor.fetchall()
        all_textures += rows

    if not all_textures:
        raise ValueError("No textures found in meta DB.")
    
    # for metadata in rows:
    #     index_textures_from_assetbundle(metadata)
    
    with Pool() as pool:
        _ = list(tqdm.tqdm(pool.imap_unordered(index_textures_from_assetbundle, all_textures, chunksize=6), total=len(all_textures), desc="Extracting textures"))


def index_assets():
    print("=== EXTRACTING ASSETS ===")
    index_lyrics()
    index_story()
    index_textures()


def index_game_strings():
    print("=== EXTRACTING GAME STRINGS ===")

    string_dump_file = os.path.join(util.config['game_folder'], "db_dump.json")

    if not os.path.exists(string_dump_file):
        print("db_dump.json not found. Skipping")

    data = util.load_json(string_dump_file)

    # TODO: Detect if strings have been shifted over.

    out_dict = {}

    for key, value in data.items():
        text_id = key
        source_text = value

        tl_item = {
            "text": "",
            "source": source_text,
            "hash": hashlib.sha256(str(source_text).encode("utf-8")).hexdigest()
        }

        out_dict[text_id] = tl_item
    
    out_path = os.path.join(util.ASSEMBLY_FOLDER_EDITING, "JPDict.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    util.save_json(out_path, out_dict)

def main():
    index_game_strings()
if __name__ == "__main__":
    main()

# TODO: Rename index to extract