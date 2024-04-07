import util
import requests
import os
import unity
import shutil

def extract_texture(hash, write_path, size):
    bundle = unity.load_asset_from_hash(hash)
    for object in bundle.objects:
        if object.type.name == "Texture2D":
            tree = object.read()
            image = tree.image
            image = image.resize(size)
            image.save(write_path)

def main():
    # Fetch existing IDs
    r = requests.get("https://discord.com/api/v9/oauth2/applications/954453106765225995/assets")
    r.raise_for_status()
    existing_assets = r.json()
    existing_chara_ids = set()
    existing_music_ids = set()

    for asset in existing_assets:
        if asset['name'].startswith("chara_"):
            existing_chara_ids.add(int(asset['name'][6:]))
        elif asset['name'].startswith("music_"):
            existing_music_ids.add(int(asset['name'][6:]))
    
    print(f"Existing chara ids: {existing_chara_ids}")
    print(f"Existing music ids: {existing_music_ids}")


    # Determine IDs currently in the game
    new_chara_ids = set()
    new_music_ids = set()
    with util.MDBConnection() as (conn, cursor):
        cursor.execute("SELECT DISTINCT chara_id FROM card_data;")
        for row in cursor.fetchall():
            if row[0] not in existing_chara_ids:
                new_chara_ids.add(row[0])
        
        cursor.execute("SELECT DISTINCT music_id FROM live_permission_data;")
        for row in cursor.fetchall():
            if row[0] not in existing_music_ids:
                new_music_ids.add(row[0])
    
    print(f"New chara ids: {new_chara_ids}")
    print(f"New music ids: {new_music_ids}")

    # Extract the textures
    shutil.rmtree("tmp/discord_assets", ignore_errors=True)
    os.makedirs("tmp/discord_assets", exist_ok=True)
    for chara_id in new_chara_ids:
        asset_name = f"%/chr_icon_{chara_id}_{chara_id}01_01"
        print(f"Fetching {asset_name}")
        with util.MetaConnection() as (conn, cursor):
            cursor.execute("SELECT h FROM a WHERE n like ?", (asset_name,))
            row = cursor.fetchall()
            if not row:
                print(f"Hash not found for {asset_name}")
                continue
            print(row)

            hash = row[0][0]
            filename = "chara_" + str(chara_id)
            extract_texture(hash, f"tmp/discord_assets/{filename}.png", (512, 560))
    
    for music_id in new_music_ids:
        asset_name = f"%/jacket_icon_l_{music_id}"
        print(f"Fetching {asset_name}")
        with util.MetaConnection() as (conn, cursor):
            cursor.execute("SELECT h FROM a WHERE n like ?", (asset_name,))
            row = cursor.fetchall()
            if not row:
                print(f"Hash not found for {asset_name}")
                continue
            print(row)

            hash = row[0][0]
            filename = "music_" + str(music_id)
            extract_texture(hash, f"tmp/discord_assets/{filename}.png", (512, 512))




if __name__ == "__main__":
    main()
