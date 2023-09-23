import util
import os
import glob
import json
import shutil
from multiprocessing import Pool
from itertools import repeat
import tqdm
import UnityPy
import io
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

# def backup_mdb():
#     print("Backing up MDB...")
#     shutil.copy(util.MDB_PATH, util.MDB_PATH + f".{round(time.time())}")

def import_mdb():
    mdb_jsons = glob.glob(util.MDB_FOLDER + "\\**\\*.json")

    with util.MDBConnection() as (conn, cursor):
        for mdb_json in mdb_jsons:
            path_segments = os.path.normpath(mdb_json).rsplit(".", 1)[0].split(os.sep)
            category = path_segments[-1]
            table = path_segments[-2]

            # Backup the table
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {util.TABLE_BACKUP_PREFIX}{table} AS SELECT * FROM {table};")

            print(f"Importing {table} {category}")
            data = util.load_json(mdb_json)

            for index, entry in data.items():

                cursor.execute(
                    f"""UPDATE {table} SET text = ? WHERE category = ? and `index` = ?;""",
                    (entry['text'], category, index)
                )

        conn.commit()
        cursor.execute("VACUUM;")
        conn.commit()

    print("Import complete.")


def clean_asset_backups():
    asset_backups = glob.glob(util.DATA_PATH + "\\**\\*.bak", recursive=True)
    print(f"Amount of backups to revert: {len(asset_backups)}")
    for asset_backup in asset_backups:
        asset_path = asset_backup.rsplit(".", 1)[0]
        if not os.path.exists(asset_path):
            print(f"Deleting {asset_backup}")
            os.remove(asset_backup)

def create_new_image_from_path_id(asset_bundle, path_id, diff_path):
    # Read the original texture
    texture_object = asset_bundle.assets[0].files[path_id]
    texture_read = texture_object.read()
    source_bytes_buffer = io.BytesIO()
    texture_read.image.save(source_bytes_buffer, format="PNG")
    source_bytes_buffer.seek(0)
    source_bytes = source_bytes_buffer.read()
    source_bytes_buffer.close()

    # Read the diff texture
    with open(diff_path, "rb") as f:
        diff_bytes = f.read()
    
    # Apply the diff
    max_len = max(len(diff_bytes), len(source_bytes))

    diff_bytes = diff_bytes.ljust(max_len, b'\x00')
    source_bytes = source_bytes.ljust(max_len, b'\x00')

    new_bytes = util.xor_bytes(diff_bytes, source_bytes)

    return new_bytes, texture_read

def import_assets():
    clean_asset_backups()

    jsons = glob.glob(util.ASSETS_FOLDER + "\\**\\*.json", recursive=True)

    with Pool() as pool:
        results = list(tqdm.tqdm(pool.imap_unordered(util.test_for_type, zip(jsons, repeat("texture")), chunksize=128), total=len(jsons), desc="Looking for textures"))

        asset_metadatas = [result[1] for result in results if result[0]]

        print(f"Found {len(asset_metadatas)} assets to replace.")

        # This becomes a pool function.
        for asset_metadata in asset_metadatas:
            hash = asset_metadata['hash']
            asset_path = util.get_asset_path(hash)
            asset_path_bak = asset_path + ".bak"

            if not os.path.exists(asset_path):
                print(f"Asset not found: {asset_path}")
                continue

            if not os.path.exists(asset_path_bak):
                shutil.copy(asset_path, asset_path_bak)
            else:
                shutil.copy(asset_path_bak, asset_path)
            
            print(f"Replacing {asset_path}")
            asset_bundle = UnityPy.load(asset_path)
            
            for texture_data in asset_metadata['textures']:
                path_id = texture_data['path_id']
                diff_path = os.path.join(util.ASSETS_FOLDER, asset_metadata['file_name'], texture_data['name'] + ".diff")

                new_bytes, texture_read = create_new_image_from_path_id(asset_bundle, path_id, diff_path)

                # Create new image
                new_image_buffer = io.BytesIO()
                new_image_buffer.write(new_bytes)
                new_image_buffer.seek(0)
                new_image = Image.open(new_image_buffer)

                # Replace the image
                texture_read.image = new_image
                texture_read.save()

                new_image_buffer.close()
            
            with open(asset_path, "wb") as f:
                f.write(asset_bundle.file.save(packer="original"))

def import_assembly():
    print("Importing assembly text...")

    jpdict_path = os.path.join(util.ASSEMBLY_FOLDER, "JPDict.json")

    if not os.path.exists(jpdict_path):
        print(f"JPDict not found: {jpdict_path} - Skipping")
        return

    jpdict = util.load_json(jpdict_path)

    game_folder = util.config.get("game_folder")

    if not game_folder:
        raise ValueError("game_folder not set in config.json")
    
    if not os.path.exists(game_folder):
        raise FileNotFoundError(f"Game folder does not exist: {game_folder}")
    
    translations_path = os.path.join(game_folder, "translations.txt")

    lines = []

    for text_id, text_data in jpdict.items():
        text = text_data['text'].replace("\r", "\\r").replace("\n", "\\n").replace("\"", "\\\"")
        lines.append(f"{text_id}\t{text}")

    with open(translations_path, "w", encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    print(f"Imported {len(lines)} lines to {translations_path}")



def main():
    if not os.path.exists(util.MDB_PATH):
        raise FileNotFoundError(f"MDB not found: {util.MDB_PATH}")

    # backup_mdb()

    import_mdb()

    import_assets()

    import_assembly()

def test():
    import_assembly()

if __name__ == "__main__":
    test()
