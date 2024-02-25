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


def autofill_factor_descriptions():
    # Prepare skill dict
    skill_name_dict = {}
    path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "47.json")
    data = util.load_json(path)
    for entry in data:
        keys = json.loads(entry["keys"])
        name = entry["text"]
        if not name:
            name = entry["source"]
        
        for key in keys:
            skill_name_dict[key[-1]] = name

    type_descr = {
        1: "SPD",
        2: "STA",
        3: "POW",
        4: "GUT",
        5: "WIS",
        6: "Skill Points",
        11: "Turf Aptitude",
        12: "Dirt Aptitude",
        21: "Runner Aptitude",
        22: "Leader Aptitude",
        23: "Betweener Aptitude",
        24: "Chaser Aptitude",
        31: "Short Aptitude",
        32: "Mile Aptitude",
        33: "Medium Aptitude",
        34: "Long Aptitude",
        61: "SPD Cap",
        62: "STA Cap",
        63: "POW Cap",
        64: "GUT Cap",
        65: "WIS Cap",
    }


    path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "172.json")
    data = util.load_json(path)

    for entry in data:
        key = json.loads(entry["keys"])[0][-1]
        factor_group_id = str(key)[:-2]

        # Fetch factor effects
        with util.MDBConnection() as (_, cursor):
            cursor.execute("SELECT target_type, value_1, value_2 FROM succession_factor_effect WHERE factor_group_id = ?", (factor_group_id,))
            rows = cursor.fetchall()

            if not rows:
                print(f"Factor group {factor_group_id} has no factor effects. Skipping.")
                continue

        effect_dict = {}

        for row in rows:
            if row[0] in effect_dict:
                continue

            effect_dict[row[0]] = (row[1], row[2])
        
        effect_types = sorted(effect_dict.keys())

        # 41: Skill
        # 51: Carnival Bonus LvX Skill - Goes away after training.
        uppies = []
        getties = []

        for effect_type in effect_types:
            if effect_type in type_descr:
                uppies.append(type_descr[effect_type])
            elif effect_type == 41:
                # Obtain skill
                skill_id = effect_dict[effect_type][0]
                skill_name = skill_name_dict.get(skill_id)
                if not skill_name:
                    print(f"Skill {skill_id} not found in skill index. Skipping effect type {effect_type}.")
                    continue
                txt = f"obtain [{skill_name}] skill hint"
                getties.append(txt)
            elif effect_type == 51:
                # Carnival bonus skill
                txt = "obtain [Carnival Bonus Lv{0}] skill. Goes away after training ends"
                getties.append(txt)

        uppies_part = ""

        if uppies:
            uppies_part = "Increases "
            if len(uppies) == 1:
                uppies_part += uppies[0]
            else:
                uppies_part += ", ".join(uppies[:-1]) + f" and {uppies[-1]}"
            uppies_part += "."
        
        getties_part = ""
        if getties:
            if len(getties) == 1:
                getties_part = getties[0]
            else:
                getties_part = ", ".join(getties[:-1]) + f" and {getties[-1]}"
            getties_part += "."
        
        if uppies_part and getties_part:
            uppies_part += "\\n"
        
        if getties_part:
            getties_part = getties_part[0].upper() + getties_part[1:]
        
        entry["text"] = uppies_part + getties_part

    util.save_json(path, data)

def autofill_chara_story_chapters():
    print("Autofilling chara story chapters (text_data/92.json)")
    path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "92.json")

    if not os.path.exists(path):
        print(f"File {path} does not exist. Skipping.")
        return
    
    data = util.load_json(path)

    for entry in data:
        key = json.loads(entry["keys"])[0][-1]
        grp = '04'
        chara = str(key)[1:5]
        chpt = str(key)[5:]

        story_path = os.path.join(util.ASSETS_FOLDER_EDITING, "story", grp, chara, f"{chpt}.json")

        if not os.path.exists(story_path):
            print(f"Story {story_path} does not exist. Skipping.")
            continue

        story_data = util.load_json(story_path)

        tl_title = story_data.get('title')

        if not tl_title or tl_title == story_data.get('source'):
            # No translation or translation is the same as the original
            continue

        entry['text'] = tl_title

    util.save_json(path, data)


def autofill_support_effects():
    print("Autofilling support effects (text_data/78.json)")
    path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "151.json")

    if not os.path.exists(path):
        print(f"File {path} does not exist. Skipping.")
        return
    
    data = util.load_json(path)

    effect_dict = {}
    for entry in data:
        if not entry.get('text'):
            continue

        effect_dict[entry['source']] = entry['text']
    
    fill_ids = [
        '298',
        '329'
    ]

    for id in fill_ids:
        path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", f"{id}.json")

        if not os.path.exists(path):
            print(f"File {path} does not exist. Skipping.")
            continue

        data = util.load_json(path)

        for entry in data:
            new_text = effect_dict.get(entry['source'])
            if not new_text:
                continue

            entry['text'] = new_text

        util.save_json(path, data)



def run():
    autofill_birthdays()
    autofill_outfit_combos()
    autofill_support_combos()
    autofill_pieces()
    autofill_chara_secret_headers()
    autofill_factor_descriptions()
    autofill_chara_story_chapters()
    autofill_support_effects()

def main():
    autofill_support_effects()
    pass

if __name__ == "__main__":
    main()
