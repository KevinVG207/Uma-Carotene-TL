import util
import os
import unicodedata
import json

def autofill_birthdays():
    json_path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "157.json")

    if not os.path.exists(json_path):
        print(f"File {json_path} does not exist. Skipping.")
        return
    
    months = {
        "1": "January",
        "2": "February",
        "3": "March",
        "4": "April",
        "5": "May",
        "6": "June",
        "7": "July",
        "8": "August",
        "9": "September",
        "10": "October",
        "11": "November",
        "12": "December"
    }

    json_data = util.load_json(json_path)

    for entry in json_data:
        birthday_jp = entry["source"]
        month, day = birthday_jp.split("月")
        day = unicodedata.normalize('NFKC', day[:-1])
        month = unicodedata.normalize('NFKC', month)
        entry["text"] = f"{months[month]} {day}"
    
    util.save_json(json_path, json_data)

INDEX_CACHE = {}
def index_category(cat_id, no_cache=False):
    global INDEX_CACHE

    if not no_cache and cat_id in INDEX_CACHE:
        return INDEX_CACHE[cat_id]

    json_path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", f"{cat_id}.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"File {json_path} does not exist.")
    
    index = {}

    json_data = util.load_json(json_path)
    for entry in json_data:
        for key in json.loads(entry["keys"]):
            if entry["text"]:
                index[key[-1]] = entry["text"]
    
    if not no_cache:
        INDEX_CACHE[cat_id] = index

    return index

def autofill_outfit_combos():
    print("Autofilling outfit combos (text_data/4.json)")

    # Index outfits and characters
    outfit_index = index_category(5)
    chara_name_index = index_category(170)

    # Load outfit combos
    json_path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "4.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"File {json_path} does not exist.")
    
    json_data = util.load_json(json_path)

    # Fill in outfit combos
    for entry in json_data:
        key = str(json.loads(entry["keys"])[0][-1])
        outfit_id = int(key[-6:])
        chara_id = int(key[-6:-2])

        if not outfit_id in outfit_index:
            print(f"Outfit {outfit_id} not found in outfit index. Skipping.")
            continue
        if not chara_id in chara_name_index:
            print(f"Character {chara_id} not found in character index. Skipping.")
            continue
        
        entry["text"] = f"{outfit_index[outfit_id]} {chara_name_index[chara_id]}"
    
    util.save_json(json_path, json_data)


def autofill_pieces():
    print("Autofilling pieces (text_data/113.json)")

    chara_name_index = index_category(170)
    
    json_path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "113.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"File {json_path} does not exist.")
    
    json_data = util.load_json(json_path)

    for entry in json_data:
        key = str(json.loads(entry["keys"])[0][-1])
        chara_id = int(key[:4])

        if not chara_id in chara_name_index:
            print(f"Character {chara_id} not found in character index. Skipping.")
            continue

        entry["text"] = f"{chara_name_index[chara_id]} Piece"
    
    util.save_json(json_path, json_data)


def main():
    # autofill_birthdays()
    autofill_outfit_combos()
    autofill_pieces()
    pass

if __name__ == "__main__":
    main()
