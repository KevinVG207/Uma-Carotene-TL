import requests
import util
from multiprocessing.pool import Pool
import os
import glob

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


def fetch_story_json(url):
    r = requests.get(url)
    r.raise_for_status()

    return r.json()


def import_external_story(local_path, url_to_github_jsons):
    # Download all jsons from github
    print("Downloading jsons from github")

    r = requests.get(url_to_github_jsons)
    r.raise_for_status()

    urls = [data['download_url'] for data in r.json()]


    with Pool(5) as pool:
        story_data = pool.map(fetch_story_json, urls)
    
    # imported_stories = {data['bundle']: data for data in story_data}
    imported_stories = {}
    imported_titles = {}
    for data in story_data:
        cur_blocks = {}
        for block in data['text']:
            cur_blocks[block['pathId']] = {
                'path_id': block['pathId'],
                'block_id': block['blockIdx'],
                'text': block['enText'],
                'name': block['enName'],
                'clip_length': block.get('newClipLength', block['origClipLength']),
                'source_clip_length': block['origClipLength'],
            }

            anim_data = block.get('animData')
            choices = block.get('choices')

            if anim_data:
                cur_data = []
                for anim in anim_data:
                    cur_data.append({
                        'orig_length': anim['origLen'],
                        'path_id': anim['pathId'],
                    })
                cur_blocks[block['pathId']]['anim_data'] = cur_data
            
            if choices:
                cur_data = []
                for choice in choices:
                    cur_data.append({
                        'text': choice['enText']
                    })
                cur_blocks[block['pathId']]['_choices'] = cur_data
                # cur_blocks[block['pathId']]['choices'] = choices
        
        imported_stories[data['bundle']] = cur_blocks
        imported_titles[data['bundle']] = data['title']

    print(imported_stories.keys())

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
        
        for block in data['data']:
            import_block = imported_stories[data['hash']].get(block['path_id'])

            if not import_block:
                print(f"Skipping {block['path_id']}, not found in github")
                continue

            block.update(import_block)

            # Fix choices
            if block.get('_choices'):
                for i, choice in enumerate(block['_choices']):
                    block['choices'][i]['text'] = choice['text']
                
                del block['_choices']

        util.save_json(local_file, data)
    
    print("Done")



def main():
    import_external_story('story/04/1026', 'https://api.github.com/repos/KevinVG207/umamusu-translate/contents/translations/story/04/1026?ref=mdb-update')

    # umapyoi_chara_ids = get_umapyoi_chara_ids()
    # apply_umapyoi_character_profiles(umapyoi_chara_ids)
    # apply_umapyoi_outfits(umapyoi_chara_ids)

if __name__ == "__main__":
    main()
