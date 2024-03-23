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
import _patch
from win32com.client import Dispatch
import copy

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


def story_data_equal(data1, data2):
    if len(data1) != len(data2):
        return False

    for i, clip in enumerate(data1):
        clip2 = data2[i]

        if clip['source'] != clip2['source']:
            return False
        
        if clip.get('choices'):
            if not clip2.get('choices'):
                return False
            
            if len(clip['choices']) != len(clip2['choices']):
                return False
            
            for j, choice in enumerate(clip['choices']):
                choice2 = clip2['choices'][j]

                if choice['source'] != choice2['source']:
                    return False

    return True


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
        if not tree.get('textData'):
            return

        tl_item['type'] = 'race'
        for text in tree['textData']:
            clip_item = {
                "text": "",
                "source": text['text'],
            }
            tl_item["data"].append(clip_item)

    else:
        tl_item['title'] = ""
        tl_item['source_title'] = tree['Title']
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

                    # "source_name_hash": hashlib.sha256(str(source_name).encode("utf-8")).hexdigest()
                }

                if text_data.get('ColorTextInfoList'):
                    clip_item['source_color'] = util.apply_colored_text(clip_item['source'], text_data['ColorTextInfoList'])

                clip_item['name'] = ""
                clip_item['source_name'] = source_name

                if text_data.get("ClipLength"):
                    clip_item["clip_length"] = text_data["ClipLength"]
                    clip_item["source_clip_length"] = text_data["ClipLength"]

                if text_data.get('ChoiceDataList'):
                    clip_item["choices"] = []
                    for choice in text_data['ChoiceDataList']:
                        choice_item = {
                            "text": "",
                            "source": choice['Text'],
                            "hash": hashlib.sha256(str(choice['Text']).encode("utf-8")).hexdigest(),
                        }
                        clip_item["choices"].append(choice_item)

                tl_item["data"].append(clip_item)

    write_path = create_write_path(tl_item['file_name'])

    os.makedirs(os.path.dirname(write_path), exist_ok=True)

    if not new:
        print(f"\nStory data {tl_item['file_name']} has changed. Creating backup and replacing.", flush=True)
        bak_path = write_path + f".{round(time.time())}"
        os.rename(write_path, bak_path)

        # Check if they are equal.
        old_data = util.load_json(bak_path)
        if story_data_equal(tl_item['data'], old_data['data']):
            # Restore translations from the old file.
            for i, old_entry in enumerate(old_data['data']):
                new_entry = tl_item['data'][i]
                old_entry['path_id'] = new_entry['path_id']

            tl_item['data'] = old_data['data']
            tl_item['title'] = old_data['title']
            print(f"\nRestored translations from {bak_path}.", flush=True)


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
            intermediate_data['data'][i]['text'] = util.apply_colored_text(line['text'], line.get('color_info'))
            intermediate_data['data'][i]['name'] = line['name']
            intermediate_data['data'][i]['clip_length'] = line['clip_length']
            if 'choices' in line:
                for j, choice in enumerate(line['choices']):
                    intermediate_data['data'][i]['choices'][j]['text'] = choice['text']
            # for key, value in line.items():
            #     intermediate_data['data'][i][key] = value
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
            data = util.json.load(f)
            if data['hash'] == hash:
                # Hash is the same, no need to update.
                return
            cached_intermediates = data['data']
    
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

    existing_meta = None

    if os.path.exists(meta_file_path):
        existing_meta = util.load_json(meta_file_path)

        shortcut_out = os.path.join(util.ASSETS_FOLDER_EDITING, file_name, hash + ".lnk")
        asset_path = util.get_asset_path(existing_meta['hash'])

        if not os.path.exists(shortcut_out):
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_out)
            shortcut.Targetpath = asset_path.replace("/", "\\")
            shortcut.save()

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
            
            shortcut_out = os.path.join(util.ASSETS_FOLDER_EDITING, file_name, existing_meta['hash'] + ".lnk")
            if os.path.exists(shortcut_out):
                os.remove(shortcut_out)
    
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

    if textures_list or existing_meta:
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
        
        # Create a shortcut to the asset bundle.
        shortcut_out = os.path.join(util.ASSETS_FOLDER_EDITING, file_name, hash + ".lnk")
        asset_path = util.get_asset_path(hash)

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_out)
        shortcut.Targetpath = asset_path.replace("/", "\\")
        shortcut.save()

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
        asset_path = util.get_asset_path(hash)

        if not os.path.exists(asset_path):
            print(f"\nTexture {file_name} not found. Skipping.")
            return

        png_out = os.path.join(out_folder, os.path.basename(file_name) + ".png")
        org_out = os.path.join(out_folder, os.path.basename(file_name) + ".org.png")
        hash_out = os.path.join(out_folder, os.path.basename(file_name) + ".hash")
        asset_bundle = UnityPy.load(asset_path)
        for texture in metadata['textures']:
            path_id = texture['path_id']
            diff_path = os.path.join(util.ASSETS_FOLDER, file_name, texture['name'] + ".diff")
            new_bytes, texture_read = _patch.create_new_image_from_path_id(asset_bundle, path_id, diff_path)
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

        cursor.execute(
            """SELECT n, h FROM a WHERE n like 'sourceresources/flash/%' ORDER BY n ASC;"""
        )
        rows = cursor.fetchall()
        all_textures += rows

        # Character "Train" buttons
        cursor.execute(
            """SELECT n, h FROM a WHERE n like 'chara/chr____/petit/%007_' ORDER BY n ASC;"""
        )
        rows = cursor.fetchall()
        all_textures += rows

        # Comics
        cursor.execute(
            """SELECT n, h FROM a WHERE n like 'outgame/comic/tex_%' ORDER BY n ASC;"""
        )
        rows = cursor.fetchall()
        all_textures += rows

        cursor.execute(
            """SELECT n, h FROM a WHERE n like 'race/racetitle/%' ORDER BY n ASC;"""
        )
        rows = cursor.fetchall()
        all_textures += rows

    if not all_textures:
        raise ValueError("No textures found in meta DB.")

    
    with Pool() as pool:
        _ = list(tqdm.tqdm(pool.imap_unordered(index_textures_from_assetbundle, all_textures, chunksize=6), total=len(all_textures), desc="Extracting textures"))

    # for metadata in all_textures:
    #     index_textures_from_assetbundle(metadata)
        

def index_flash_text_from_assetbundle(metadata):
    file_name = metadata[0]
    hash = metadata[1]

    file_path = os.path.join(util.DATA_PATH, hash[:2], hash)

    if not os.path.exists(file_path):
        print(f"\nUser has not downloaded flash {file_name}. Skipping.")
        return

    meta_file_path = os.path.join(util.FLASH_FOLDER_EDITING, file_name, os.path.basename(file_name) + ".json")

    # TODO: Make this better
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
            print(f"\nFlash {file_name} has changed. Creating backup and replacing.", flush=True)
            shutil.copy(meta_file_path, meta_file_path + f".{round(time.time())}")

    try:
        root = unity.load_assetbundle(file_path)
    except:
        print(f"\nError loading flash {file_name}. Skipping.")
        return
    
    tl_dict = {}

    for asset in root.assets_file.objects.values():
        if asset.type.name == "MonoBehaviour":
            if not asset.serialized_type.nodes:
                continue
            # Read the mono behaviour.
            tree = asset.read_typetree()
            if not tree.get("_motionParameterGroup"):
                continue
            mpg = tree["_motionParameterGroup"]
            if not mpg.get("_motionParameterList"):
                continue
            mpl = mpg["_motionParameterList"]
            for ele in mpl:
                if not ele.get("_textParamList"):
                    continue
                tpl = ele["_textParamList"]
                for tpl_ele in tpl:
                    if not tpl_ele.get("_text"):
                        continue
                    source = tpl_ele["_text"]
                    source_hash = hashlib.sha256(str(source).encode("utf-8")).hexdigest()
                    path_id = str(asset.path_id)
                    mpl_id = ele["_id"]
                    tpl_name = tpl_ele["_objectName"]
                    source_dict = {
                        "_text": source,
                        "_positionOffset": tpl_ele.get("_positionOffset"),
                        "_scale": tpl_ele.get("_scale"),
                    }
                    transl_dict = copy.deepcopy(source_dict)
                    transl_dict['hash'] = source_hash

                    if not tl_dict.get(path_id):
                        tl_dict[path_id] = {}
                    path_dict = tl_dict[path_id]
                    if not path_dict.get(mpl_id):
                        path_dict[mpl_id] = {}
                    mpl_dict = path_dict[mpl_id]
                    if not mpl_dict.get(tpl_name):
                        mpl_dict[tpl_name] = {}
                    tpl_dict = mpl_dict[tpl_name]
                    tpl_dict['source'] = source_dict
                    tpl_dict['tl'] = transl_dict

    if tl_dict:
        os.makedirs(os.path.dirname(meta_file_path), exist_ok=True)
        with open(meta_file_path, "w", encoding='utf-8') as f:
            f.write(json.dumps(
                {
                    "type": "flash",
                    "version": version.VERSION,
                    "file_name": file_name,
                    "hash": hash,
                    "new": True,
                    "data": tl_dict,
                }, indent=4, ensure_ascii=False
            ))

def index_flash():
    all_textures = []
    with util.MetaConnection() as (_, cursor):
        cursor.execute(
            """SELECT n, h FROM a WHERE n like 'uianimation/flash/%' ORDER BY n ASC;"""
        )
        rows = cursor.fetchall()
        all_textures += rows
    
    if not all_textures:
        return
    
    with Pool() as pool:
        _ = list(tqdm.tqdm(pool.imap_unordered(index_flash_text_from_assetbundle, all_textures, chunksize=16), total=len(all_textures), desc="Extracting flash"))
    # for metadata in util.tqdm(all_textures, desc="Extracting flash"):
    #     index_flash_text_from_assetbundle(metadata)


def index_assets():
    print("=== EXTRACTING ASSETS ===")
    index_lyrics()
    index_story()
    index_textures()
    index_flash()


def index_jpdict():
    print("=== Indexing JPDict ===")
    # Load existing translations
    tl_file = os.path.join(util.ASSEMBLY_FOLDER, "JPDict.json")
    if not os.path.exists(tl_file):
        tl_data = {}
    else:
        tl_data = util.load_json(tl_file)

    string_dump_file = os.path.join(util.get_game_folder(), "assembly_dump.json")

    if not os.path.exists(string_dump_file):
        print("assembly_dump.json not found. Skipping")
        return

    new_data = util.load_json(string_dump_file)

    new_dict = {}

    for key, value in new_data.items():
        text_id = key
        source_text = value

        tl_item = {
            "text": "",
            "source": source_text,
            "hash": hashlib.sha256(str(source_text).encode("utf-8")).hexdigest()
        }

        new_dict[text_id] = tl_item
    
    newly_added = {}
    changed = {}

    for key in new_dict:
        if key in tl_data:
            new_data = new_dict[key]
            old_data = tl_data[key]

            if new_data['hash'] == old_data['hash']:
                new_data['text'] = old_data['text']
                new_dict[key] = new_data
            else:
                changed[key] = {
                    "old": old_data.get('source') or old_data.get('hash'),
                    "new": new_data['source'],
                    "old_text": old_data['text'],
                }
            
        else:
            newly_added[key] = new_dict[key]['source']
    
    if newly_added:
        os.makedirs("dump", exist_ok=True)
        cur_time_str = round(time.time())
        with open(f"dump/new_JPDict.{cur_time_str}.json", "w", encoding="utf-8") as f:
            f.write(util.json.dumps(newly_added, indent=4, ensure_ascii=False, sort_keys=True)
        )
        with open(f"dump/changed_JPDict.{cur_time_str}.json", "w", encoding="utf-8") as f:
            f.write(util.json.dumps(changed, indent=4, ensure_ascii=False, sort_keys=True)
        )
    # org_data_keys = list(tl_data.keys())
    # new_data_keys = list(new_dict.keys())
    # ignore_list = set()
    # combined_dict = {}

    # for new_key in new_data_keys:
    #     if new_key.endswith("00"):
    #         print(new_key)
    #     new_data = new_dict[new_key]
    #     combined_dict[new_key] = new_data

    #     for org_key in [org_key for org_key in org_data_keys if org_key not in ignore_list]:
    #         org_data = tl_data[org_key]

    #         if new_data['hash'] == org_data['hash']:
    #             ignore_list.add(org_key)
    #             org_data['source'] = new_data['source']
    #             combined_dict[new_key] = org_data
    #             break

    out_path = os.path.join(util.ASSEMBLY_FOLDER_EDITING, "JPDict.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    util.save_json(out_path, new_dict)

    return {tl_entry['hash']: tl_entry['source'] for tl_entry in new_dict.values()}


def index_hashed(potential_hash_dict):
    print("=== Indexing Hashed ===")

    # Augment the dict
    dict_values = list(potential_hash_dict.values()) if potential_hash_dict else []  # TODO: Check if this works as intended
    for source in dict_values:
        if len(source) == 2:
            new_source = f"{source[0]} {source[1]}"
            new_hash = hashlib.sha256(new_source.encode("utf-8")).hexdigest()
            potential_hash_dict[new_hash] = new_source

    # These can only be extracted from existing translations.
    new_hashed_file = os.path.join(util.ASSEMBLY_FOLDER, "hashed.json")

    if not os.path.exists(new_hashed_file):
        print("hashed.json not found. Skipping")
        return
    
    new_hashed_data = util.load_json(new_hashed_file)

    existing_hashed_data = []
    existing_hashed_file = os.path.join(util.ASSEMBLY_FOLDER_EDITING, "hashed.json")
    if os.path.exists(existing_hashed_file):
        existing_hashed_data = util.load_json(existing_hashed_file)
    
    existing_hash_set = set()
    for hashed_entry in existing_hashed_data:
        cur_hash = hashed_entry.get('hash')
        if not cur_hash:
            cur_hash = hashlib.sha256(hashed_entry['source'].encode("utf-8")).hexdigest()
        
        existing_hash_set.add(cur_hash)

    for hashed_entry in new_hashed_data:
        if hashed_entry['hash'] in existing_hash_set:
            for existing_data in existing_hashed_data:
                existing_hash = existing_data.get('hash') if existing_data.get('hash') else hashlib.sha256(existing_data['source'].encode("utf-8")).hexdigest()
                if existing_hash == hashed_entry['hash']:
                    existing_data['text'] = hashed_entry['text']
                    break
            continue

        tl_entry = {
            "hash": hashed_entry['hash'],
            "text": hashed_entry['text']
        }

        if hashed_entry['hash'] in potential_hash_dict:
            tl_entry['source'] = potential_hash_dict[hashed_entry['hash']]
            del tl_entry['hash']

        existing_hashed_data.append(tl_entry)
    
    out_path = os.path.join(util.ASSEMBLY_FOLDER_EDITING, "hashed.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    util.save_json(out_path, existing_hashed_data)




def index_assembly():
    print("=== EXTRACTING ASSEMBLY STRINGS ===")
    hash_dict = index_jpdict()
    index_hashed(hash_dict)


def main():
    # _patch.clean_asset_backups()
    # index_story()
    index_textures()
    pass

if __name__ == "__main__":
    main()

# TODO: Rename index to extract