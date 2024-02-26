import requests
import util
from multiprocessing.pool import Pool
import os
import glob
import json
import datetime
from selenium import webdriver
import time
import re

MISSIONS_JSONS = [
    "66",
    "67",
]

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
        if not value:  # No translation
            continue

        key = f"[{category}, {chara_id}]"
        for entry in json_data:
            if key in entry["keys"]:
                entry["text"] = value.strip()
                entry['new'] = False
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


def apply_umapyoi_vas():
    va_dict = {}

    r = requests.get("https://umapyoi.net/api/v1/va")
    r.raise_for_status()
    data = r.json()

    for va_data in data.values():
        if not va_data.get('name_en'):
            continue
        if not va_data.get('characters_game'):
            continue

        for chara_id in va_data['characters_game']:
            va_dict[chara_id] = va_data['name_en']
    
    path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "7.json")
    data = util.load_json(path)

    for entry in data:
        key = json.loads(entry['keys'])[0][1]

        if va_dict.get(key):
            entry['prev_text'] = entry['text']
            entry['text'] = va_dict[key]
            entry['new'] = False

    util.save_json(path, data)


def apply_umapyoi_supports():
    print("Importing support names")
    r = requests.get("https://umapyoi.net/api/v1/support")
    r.raise_for_status()
    data = r.json()

    support_dict = {d['id']: d['title_en'] for d in data if d.get('title_en')}

    path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "76.json")
    data = util.load_json(path)

    for entry in data:
        key = json.loads(entry['keys'])[0][1]

        if support_dict.get(key):
            entry['prev_text'] = entry['text']
            entry['text'] = support_dict[key]
            entry['new'] = False

    util.save_json(path, data)





def get_umapyoi_chara_ids():
    # Fetch all character IDs

    r = requests.get("https://umapyoi.net/api/v1/character")
    r.raise_for_status()

    data = r.json()

    chara_ids = [chara["game_id"] for chara in data if chara.get("game_id")]

    return chara_ids


def fetch_story_json(url):
    r = requests.get(url)
    r.raise_for_status()

    return r.json()

def import_external_story(local_path, url_to_github_jsons, use_order=False, skip_first=False):
    # Download all jsons from github
    print("Downloading jsons from github")

    r = requests.get(url_to_github_jsons + local_path)
    r.raise_for_status()

    urls = [data['download_url'] for data in r.json()]


    with Pool(5) as pool:
        story_data = pool.map(fetch_story_json, urls)

    if local_path.startswith("story/"):
        _import_external_story(local_path, story_data, use_order, skip_first)
    elif local_path.startswith("race/"):
        _import_external_race_story(local_path, story_data)


def _import_external_race_story(local_path, story_data):
    print("Importing external race story")
    imported_stories = {}
    for data in story_data:
        tl_dict = {}
        for block in data['text']:
            tl_dict[block['jpText']] = block['enText']
        imported_stories[data['bundle']] = tl_dict
    
    # Load local story data
    print("Loading local story data")
    local_files = glob.glob(os.path.join(util.ASSETS_FOLDER_EDITING, local_path) + "/*.json")

    for local_file in local_files:
        data = util.load_json(local_file)

        file_name = os.path.basename(local_file)
        
        if not data['hash'] in imported_stories:
            print(f"Skipping {file_name}, not found in github")
            continue

        print(f"Merging {file_name}")

        for block in data['data']:
            import_en = imported_stories[data['hash']].get(block['source'])

            if not import_en:
                print(f"Skipping {block['source']}, not found in github")
                continue

            block['text'] = import_en
        
        util.save_json(local_file, data)

    print("Done")



def _import_external_story(local_path, story_data, use_order=False, skip_first=False):
    print("Importing external story")
    # imported_stories = {data['bundle']: data for data in story_data}
    imported_stories = {}
    imported_stories_list = {}
    imported_titles = {}
    for data in story_data:
        cur_blocks = {}
        cur_blocks_list = []
        for block in data['text']:
            cur_blocks[block['pathId']] = {
                'path_id': block['pathId'],
                'block_id': block['blockIdx'],
                'text': block['enText'],
                'name': block['enName'],
                'source': block['jpText'],
            }

            if block.get('title') and block['title'] != cur_blocks[block['pathId']]['source_title']:
                cur_blocks[block['pathId']]['title'] = block['title']

            if block.get('newClipLength'):
                cur_blocks[block['pathId']]['clip_length'] = block['newClipLength']
            
            if block.get('origClipLength'):
                cur_blocks[block['pathId']]['source_clip_length'] = block['origClipLength']

            choices = block.get('choices')

            if choices:
                cur_data = []
                for choice in choices:
                    cur_data.append({
                        'text': util.remove_size_tags(choice['enText'])
                    })
                cur_blocks[block['pathId']]['_choices'] = cur_data
                # cur_blocks[block['pathId']]['choices'] = choices

            cur_blocks_list.append(cur_blocks[block['pathId']])
        
        imported_stories[data['bundle']] = cur_blocks
        imported_stories_list[data['bundle']] = cur_blocks_list
        imported_titles[data['bundle']] = data['title']

    # print(imported_stories.keys())

    # Load local story data
    print("Loading local story data")
    local_files = glob.glob(os.path.join(util.ASSETS_FOLDER_EDITING, local_path) + "/*.json")

    for local_file in local_files:
        data = util.load_json(local_file)

        file_name = os.path.basename(local_file)
        
        if not data['hash'] in imported_stories:
            print(f"Skipping {file_name}, not found in github")
            continue

        print(f"Merging {file_name}")

        if data['hash'] in imported_titles:
            data['title'] = imported_titles[data['hash']]
        
        for i, block in enumerate(data['data']):
            if skip_first and i == 0:
                continue

            if use_order:
                if skip_first:
                    real_i = i - 1
                else:
                    real_i = i
                import_block = imported_stories_list[data['hash']][real_i]
            else:
                import_block = imported_stories[data['hash']].get(block['path_id'])

            if not import_block:
                print(f"Skipping {block['path_id']}, not found in github")
                continue

            if import_block.get('source') != block['source']:
                print(f"Skipping {block['path_id']}, source text mismatch")
                print(f"Local: {block['source']}")
                print(f"Import: {import_block.get('source')}")
                continue

            if use_order:
                tmp_path_id = block['path_id']

            block.update(import_block)

            if use_order:
                block['path_id'] = tmp_path_id

            # Fix choices
            if block.get('_choices'):
                for i, choice in enumerate(block['_choices']):
                    block['choices'][i]['text'] = choice['text']
                
                del block['_choices']

        util.save_json(local_file, data)
    
    print("Done")


def apply_gametora_skills():
    print("Importing GameTora skills")

    r = requests.get("https://gametora.com/loc/umamusume/skills.json")
    r.raise_for_status()

    gt_data = r.json()

    gt_name_dict = {data['name_ja']: data['name_en'] for data in gt_data if data.get('name_en')}
    gt_desc_dict = {data['id']: data['desc_en'] for data in gt_data if data.get('desc_en')}

    name_override_dict = {
        "fb9bf8950771ef57b6e26dcbe622377cf1d6abb71d36a0f8bd4da901161d8bd9": "U=ma²"
    }

    # Load local skill data
    print("Skill names")

    prefix = os.path.join(util.MDB_FOLDER_EDITING, "text_data")
    name_files = [
        "47",
        "147"
    ]

    for name_file in name_files:
        data = util.load_json(os.path.join(prefix, f"{name_file}.json"))

        for entry in data:
            prev_text = entry.get('prev_text')
            if gt_name_dict.get(entry['source']):
                entry['prev_text'] = prev_text
                entry['text'] = gt_name_dict[entry['source']]
                entry['new'] = False
            if name_override_dict.get(entry['hash']):
                entry['prev_text'] = prev_text
                entry['text'] = name_override_dict[entry['hash']]
                entry['new'] = False

        util.save_json(os.path.join(prefix, f"{name_file}.json"), data)

    print("Skill descriptions")
    desc_data = util.load_json(os.path.join(prefix, "48.json"))

    for entry in desc_data:
        keys = json.loads(entry['keys'])
        skill_id = keys[0][1]
        if skill_id in gt_desc_dict:
            cur_desc = gt_desc_dict[skill_id]
            cur_desc = util.add_period(cur_desc)
            entry['prev_text'] = entry['text']
            entry['text'] = cur_desc
            entry['new'] = False

            if 'retranslation is pending' in entry['text']:
                entry['text'] = ""
    
    util.save_json(os.path.join(prefix, "48.json"), desc_data)

    print("Done")


def fetch_skill_translations():
    path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "47.json")
    data = util.load_json(path)
    tl_dict = {}
    for entry in data:
        tl_dict[entry['source']] = entry['text']

    return tl_dict


def scrape_missions():
    driver = webdriver.Firefox()

    # Get story event URLs
    driver.get("https://gametora.com/umamusume/events/story-events")
    while not driver.execute_script("""return document.querySelector("[class^='utils_umamusume_']");""") and time.perf_counter() - t0 < 6:
        time.sleep(1.0)
    time.sleep(1.0)
    
    urls = driver.execute_script(
"""
let out = [];
let ele = document.querySelector("[class^='utils_umamusume_']");
let elements = ele.querySelectorAll("a");
for (let i = 0; i < elements.length; i++) {
    out.push(elements[i].href);
}
return out;
""")
    
    urls = set(urls)
    urls = list(urls)

    current_year = datetime.datetime.now().year
    start_year = 2021
    urls += [
        "daily",
        "main",
        "permanent"
    ]
    urls += [f"history-{year}" for year in range(start_year, current_year + 1)]

    out_dict = {}

    for url in set(urls):
        if not url.startswith("http"):
            url = f"https://gametora.com/umamusume/missions/{url}"

        driver.get(url)

        t0 = time.perf_counter()
        while not driver.execute_script("""return document.querySelector("[class^='missions_row_text_']");""") and time.perf_counter() - t0 < 6:
            time.sleep(1.0)
        time.sleep(2.0)
        ele = driver.execute_script("""
            let skill_dict = arguments[0];
            let out = [];
            let elements = document.querySelectorAll("[class^='missions_row_text_']");
            for (let i = 0; i < elements.length; i++) {
                if (elements[i].children.length != 2) {
                    continue;
                }
                let jp = elements[i].children[0].innerText;
                let en_element = elements[i].children[1];
                let skill_elements = en_element.querySelectorAll("[aria-expanded='false']");
                for (let j = 0; j < skill_elements.length; j++) {
                    let skill_name = skill_elements[j].innerText;
                    if (skill_dict.hasOwnProperty(skill_name)) {
                        skill_elements[j].textContent = skill_dict[skill_name];
                    }
                }
                let en = en_element.innerText;
                out.push([jp, en]);
            }
            return out;
        """, fetch_skill_translations())

        for e in ele:
            out_dict[e[0]] = e[1]
    
    driver.close()

    return out_dict

def scrape_title_missions():
    driver = webdriver.Firefox()

    driver.get("https://gametora.com/umamusume/trainer-titles")

    t0 = time.perf_counter()
    while not driver.execute_script("""return document.querySelector("[class^='titles_table_row_']");""") and time.perf_counter() - t0 < 6:
        time.sleep(1.0)
    time.sleep(1.0)

    data = driver.execute_script(
"""
let skill_dict = arguments[0];
let out = {};
let elements = document.querySelectorAll("[class^='titles_table_row_']");
for (let i = 0; i < elements.length; i++) {
    let src = elements[i].querySelector("img").src;
    let segments = src.split("_");
    let id = segments[segments.length - 1].split(".")[0];

    // Replace skill names
    let descr_element = elements[i].querySelector("[class^='titles_table_desc_']");
    let skill_elements = descr_element.querySelectorAll("[aria-expanded='false']");
    for (let j = 0; j < skill_elements.length; j++) {
        let skill_name = skill_elements[j].innerText;
        if (skill_dict.hasOwnProperty(skill_name)) {
            skill_elements[j].textContent = skill_dict[skill_name];
        }
    }

    let descr = descr_element.innerText;
    out[id] = descr;
}
return out;
""", fetch_skill_translations())
    return data

def apply_gametora_missions():
    print("Importing GameTora missions")

    mission_data = scrape_missions()

    if not mission_data:
        print("Failed to scrape missions")
        return

    # Load local mission data
    for json_file in MISSIONS_JSONS:
        path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", f"{json_file}.json")
        data = util.load_json(path)

        for entry in data:
            source = entry['source'].replace("\n", "").replace("\\n", "")
            if source in mission_data:
                entry['prev_text'] = entry['text']
                entry['text'] = util.add_period(mission_data[source])
                entry['new'] = False

        util.save_json(path, data)

    print("Done")

def apply_gametora_title_missions():
    print("Importing GameTora title missions")

    # {ID: EN}
    mission_data = scrape_title_missions()

    if not mission_data:
        print("Failed to scrape missions")
        return
    

    with util.MDBConnection() as (conn, cursor):
        new_dict = {}
        for key in mission_data:
            cursor.execute(
                """
                SELECT id FROM mission_data WHERE item_id = ?;
                """,
                (key,)
            )
            rows = cursor.fetchall()
            if not rows:
                continue
            for row in rows:
                new_id = str(row[0])
                if new_id.startswith("20"):
                    continue
                new_dict[new_id] = mission_data[key]
        mission_data.update(new_dict)


    # Load local mission data
    for json_file in MISSIONS_JSONS:
        path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", f"{json_file}.json")
        data = util.load_json(path)

        for entry in data:
            keys = json.loads(entry['keys'])
            for key in keys:
                key = str(key[1])
                if mission_data.get(key):
                    entry['prev_text'] = entry['text']
                    entry['text'] = util.add_period(mission_data[key])
                    entry['new'] = False
                    break

        util.save_json(path, data)
    
    print("Done")


def main():
    # import_external_story('story/04/1047', 'https://api.github.com/repos/KevinVG207/umamusu-translate/contents/translations/')
    # import_external_story('story/04/1089', 'http://localhost:8000/repos/KevinVG207/umamusu-translate/contents/translations/')
    # import_external_story('race/02/0001', 'http://localhost:8000/repos/KevinVG207/umamusu-translate/contents/translations/')
    # import_external_story('story/02/0005', 'https://api.github.com/repos/noccu/umamusu-translate/contents/translations/')
    # import_external_story('story/02/0006', 'http://localhost:8000/repos/KevinVG207/umamusu-translate/contents/translations/', use_order=True, skip_first=True)
    # import_external_story('race/02/0005', 'https://api.github.com/repos/noccu/umamusu-translate/contents/translations/')
    # import_external_story('race/02/0006', 'https://api.github.com/repos/noccu/umamusu-translate/contents/translations/')


    umapyoi_chara_ids = get_umapyoi_chara_ids()
    apply_umapyoi_character_profiles(umapyoi_chara_ids)
    apply_umapyoi_outfits(umapyoi_chara_ids)
    apply_umapyoi_vas()
    apply_umapyoi_supports()

    apply_gametora_skills()
    apply_gametora_missions()
    apply_gametora_title_missions()
    pass

if __name__ == "__main__":
    main()
