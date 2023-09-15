# Categories to use:
# Self-intros: 163
# Slogan: 144
# Ears: 166
# Tail: 167
# Strengths: 164
# Weaknesses: 165
# Family: 169

import requests
import util
from multiprocessing.pool import Pool
import os

def fetch_chara_data(chara_id):
    out = (chara_id, {})
    r = requests.get(f"https://umapyoi.net/api/v1/character/{chara_id}")

    if not r.ok:
        return out
    
    convert_map = {
        "profile": 163,
        "slogan": 144,
        "ears_fact": 166,
        "tail_fact": 167,
        "strengths": 164,
        "weaknesses": 165,
        "family_fact": 169
    }

    data = r.json()

    for key, category in convert_map.items():
        if data.get(key):
            out[1][category] = data[key]
    
    return out

def import_category(category, data):
    print(f"Importing text category {category}")

    json_path = util.MDB_FOLDER_EDITING + f"text_data/{category}.json"

    if not os.path.exists(json_path):
        print(f"Skipping {category}, file not found. Run _update_local.py first.")
        return

    json_data = util.load_json(json_path)

    for chara_id, value in data:
        key = f"[{category}, {chara_id}]"
        for entry in json_data:
            if key in entry["keys"]:
                entry["text"] = value.strip()
                break
        else:
            print(f"WARN: Couldn't find {key} in {category}.json")
    
    util.save_json(json_path, json_data)


def apply_umapyoi_character_profiles(chara_ids):
    # Fetch all character data
    print("Fetching character data")
    with Pool(5) as pool:
        chara_data = pool.map(fetch_chara_data, chara_ids)

    # Filter out characters with no data
    chara_data = [chara for chara in chara_data if chara[1]]

    # Convert to category data
    category_data = {}
    for chara in chara_data:
        for category, value in chara[1].items():
            tup = (chara[0], value)
            if category in category_data:
                category_data[category].append(tup)
            else:
                category_data[category] = [tup]
    
    # Update intermediate data per category
    for category, data in category_data.items():
        import_category(category, data)


def fetch_outfits(chara_id):
    out = []
    r = requests.get(f"https://umapyoi.net/api/v1/outfit/character/{chara_id}")
    
    if not r.ok:
        return out
    
    if r.status_code == 204:
        # No outfits
        return out
    
    data = r.json()

    for outfit in data:
        out.append((outfit['id'], outfit['title_en']))
    
    return out



def apply_umapyoi_outfits(chara_ids):
    # Fetch outfits
    outfit_data = []

    for chara_id in chara_ids:
        outfit_data.append(fetch_outfits(chara_id))
    
    proper_outfit_list = []
    for outfit_list in outfit_data:
        if not outfit_list:
            continue
        for outfit in outfit_list:
            proper_outfit_list.append(outfit)
    
    # Update intermediate data
    import_category(5, proper_outfit_list)



def get_umapyoi_chara_ids():
    # Fetch all character IDs

    r = requests.get("https://umapyoi.net/api/v1/character")
    r.raise_for_status()

    data = r.json()

    chara_ids = [chara["game_id"] for chara in data if chara.get("game_id")]

    return chara_ids


def main():
    umapyoi_chara_ids = get_umapyoi_chara_ids()
    # apply_umapyoi_character_profiles(umapyoi_chara_ids)
    apply_umapyoi_outfits(umapyoi_chara_ids)

if __name__ == "__main__":
    main()
