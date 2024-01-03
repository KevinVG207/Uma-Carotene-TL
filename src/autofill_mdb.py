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

def autofill_support_combos():
    print("Autofilling support combos (text_data/75.json)")

    # Index supports and characters
    support_index = index_category(76)
    chara_name_index = index_category(77)

    json_path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "75.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"File {json_path} does not exist.")
    
    json_data = util.load_json(json_path)

    for entry in json_data:
        key = str(json.loads(entry["keys"])[0][-1])
        
        support_name = support_index.get(int(key))
        if not support_name:
            print(f"Support {key} not found in support index 76. Skipping.")
            continue

        chara_name = chara_name_index.get(int(key))
        if not chara_name:
            print(f"Character {key} not found in character index 77. Skipping.")
            continue
        
        entry["text"] = f"{support_name} {chara_name}"

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

def autofill_chara_secret_headers():
    chara_path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "6.json")

    if not os.path.exists(chara_path):
        print(f"File {chara_path} does not exist. Skipping.")
        return

    chara_name_data = util.load_json(chara_path)

    char_dict = {}
    for entry in chara_name_data:
        jp = entry["source"]
        en = entry["text"]
        if not en:
            continue
        char_dict[jp] = en
    
    json_path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "68.json")

    if not os.path.exists(json_path):
        print(f"File {json_path} does not exist. Skipping.")
        return
    
    json_data = util.load_json(json_path)

    for entry in json_data:
        source = entry["source"]

        num = source[-1]
        num = unicodedata.normalize('NFKC', num)  # Turn circle numbers into normal numbers

        if not num.isnumeric():
            continue

        rest = source[:-1]

        is_secret = False

        if rest.endswith("のヒミツ"):
            rest = rest[:-4]
            is_secret = True

        char_name = char_dict.get(rest)
        if not char_name:
            print(f"Character {rest} not found in character index. Skipping.")
            continue

        out = f"{char_name} "
        if is_secret:
            out += "Secret "
        
        out += f"#{num}"

        entry["text"] = out

    util.save_json(json_path, json_data)



def main():
    # autofill_birthdays()
    autofill_outfit_combos()
    autofill_support_combos()
    autofill_pieces()
    autofill_chara_secret_headers()
    pass

if __name__ == "__main__":
    main()
