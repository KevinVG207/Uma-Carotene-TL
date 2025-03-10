import math
import util
from tqdm import tqdm
from itertools import repeat
import json


FONT = util.prepare_font()


def add_slogan_tag(text):
    return "<slogan>" + text

def add_rbr_tag(text):
    return "<rbr>" + text

def add_nb_tag(text):
    return "<nb>" + text


def scale_to_width(text, max_width, def_size=None):
    tmp_text = util.filter_tags(text)

    cur_width = util.get_text_width(tmp_text, FONT)
    if cur_width <= max_width:
        return text
    
    if def_size:
        scale_factor = math.floor(max_width / cur_width * def_size)
        return f"<size={scale_factor}>{text}</size>"
    
    scale_factor = math.floor(max_width / cur_width * 100)
    return f"<sc={scale_factor}>{text}"


def scale_to_box(text, max_width, lines, line_spacing=1.00):
    # Find text scaling so it fits in a box with wrapping on spaces.
    # TODO: Find a way to handle tags.

    global FONT
    line_height = 1000 * line_spacing
    max_height = line_height * lines

    scale = 100
    hyphenation = False
    while True:
        true_scale = scale / 100.
        lines = util.wrap_text_to_width(text, max_width, FONT, true_scale, hyphenation)
        height = (1 + lines.count("\n")) * 1000 * true_scale

        if height <= max_height:
            break

        if not hyphenation:
            hyphenation = True
            continue

        scale -= 1
        if scale <= 0:
            print("Warning: Couldn't scale text to fit box")
            break
    
    text = lines.replace("\n", "<br>")

    if scale < 100:
        text = f"<sc={scale}>{text}"

    return text


PP_FUNCS = {
    # Slogans
    ("text_data", "144"): [(add_rbr_tag, None)],
    
    # Support cards
    ("text_data", "76"): [(scale_to_width, (14800,))],

    # Outfits
    ("text_data", "5"): [(scale_to_width, (14800,))],

    # VA names
    ("text_data", "7"): [(scale_to_width, (9200,)), (add_nb_tag, None)],

    # Chara names
    ("text_data", "6"): [(scale_to_width, (9500,))],
    ("text_data", "77"): [(scale_to_width, (9500,))],
    ("text_data", "78"): [(scale_to_width, (9500,))],
    ("text_data", "170"): [(scale_to_width, (9500,))],

    # Skills
    ("text_data", "47"): [(scale_to_width, (13110,))],
    ("text_data", "48"): [(scale_to_box, (18630, 4)), (add_rbr_tag, None)],

    # Missions
    ("text_data", "66"): [(scale_to_box, (15800, 2)), (add_rbr_tag, None)],
    ("text_data", "67"): [(scale_to_box, (15800, 2)), (add_rbr_tag, None)],

    # Factors
    ("text_data", "147"): [(scale_to_width, (12555,))],

    # Secrets/Comics/Tazuna
    ("text_data", "69"): [("filter", (8000, 9999)), (scale_to_box, (20000, 4)), (add_rbr_tag, None)],

    # Story chapter titles
    ("text_data", "92"): [(scale_to_width, (19120,)), (add_nb_tag, None)],
    ("text_data", "94"): [(scale_to_width, (19120,)), (add_nb_tag, None)],
    ("text_data", "191"): [(scale_to_width, (19120,)), (add_nb_tag, None)],
    ("text_data", "222"): [(scale_to_width, (19120,)), (add_nb_tag, None)],

    # Story titles
    # TODO: Check if the width is correct
    ("text_data", "189"): [(scale_to_width, (19120,)), (add_nb_tag, None)],
    ("text_data", "214"): [(scale_to_width, (19120,)), (add_nb_tag, None)],
}


def process_mdb(args):
    entry, key, file_key = args
    key = int(key)

    # Clean up any previous processed data
    if 'processed' in entry:
        del entry['processed']

    if not entry.get('text'):
        return entry

    if file_key in PP_FUNCS:
        processed = entry['text']
        for func in PP_FUNCS[file_key]:
            pp_func, pp_args = func

            # Filter keys
            if pp_func == "filter":
                start, end = pp_args
                if key in range(start, end + 1):
                    continue
                else:
                    break

            if pp_args:
                processed = pp_func(processed, *pp_args)
            else:
                processed = pp_func(processed)
            
        if processed != entry['text']:
            entry['processed'] = processed
    
    return entry


def fix_mdb():
    for mdb_json_path in tqdm(util.get_tl_mdb_jsons(), desc="Postprocessing MDB"):
        key = util.split_mdb_path(mdb_json_path)
        data = util.load_json(mdb_json_path)

        keys, values = zip(*data.items())

        if key in PP_FUNCS:
            with util.UmaPool() as p:
                values = p.map(process_mdb, zip(values, keys, repeat(key)))
            
            data = dict(zip(keys, values))
        
        else:
            for i, entry in enumerate(values):
                data[keys[i]] = process_mdb((entry, keys[i], key))


        # for entry in data.values():
        #     # Clean up any previous processed data
        #     if 'processed' in entry:
        #         del entry['processed']

        #     if not entry.get('text'):
        #         continue

        #     if key in PP_FUNCS:
        #         processed = entry['text']
        #         for func in PP_FUNCS[key]:
        #             pp_func, pp_args = func

        #             if pp_args:
        #                 processed = pp_func(processed, *pp_args)
        #             else:
        #                 processed = pp_func(processed)
                    
        #         if processed != entry['text']:
        #             entry['processed'] = processed
        
        util.save_json(mdb_json_path, data)

def _fix_story(story_data):
    json_data, path = story_data

    if json_data['file_name'].startswith("home/"):
        # Process name.
        for block in json_data['data']:
            if block.get('name'):
                if block.get('name_processed'):
                    del block['name_processed']
                proc_name = scale_to_width(block['name'], 10350)
                if proc_name != block['name']:
                    block['name_processed'] = proc_name
        util.save_json(path, json_data)
        return

    for block in json_data['data']:
        # Add story tags
        # if block.get('text'):
        #     tmp_text = block['text']
        #     tmp_text = '<story>' + tmp_text.replace("\n", "\n<story>")
        #     block['processed'] = tmp_text

        # Process name
        if block.get('name'):
            if block.get('name_processed'):
                del block['name_processed']
            proc_name = scale_to_width(block['name'], 12420)
            if proc_name != block['name']:
                block['name_processed'] = proc_name
        
        if block.get('choices'):
            for choice in block['choices']:
                # Process choice text
                if choice.get('processed'):
                    del choice['processed']

                if choice.get('text'):
                    proc_text = scale_to_width(choice['text'], 20150, 44)
                    if proc_text != choice['text']:
                        choice['processed'] = proc_text

    util.save_json(path, json_data)


def fix_stories(story_datas):
    with util.UmaPool() as pool:
        _ = list(util.tqdm(pool.imap_unordered(_fix_story, story_datas, chunksize=2), total=len(story_datas), desc="Postprocessing stories"))
    # for story_data in tqdm(story_datas, desc="Postprocessing stories"):
    #     _fix_story(story_data)

def fix_assets():
    asset_dict = util.get_assets_type_dict()
    # fix_flash(asset_dict.get('flash', []))
    # fix_textures(asset_dict.get('texture', []))
    fix_stories(asset_dict.get('story', []))


def do_postprocess():
    print("Postprocessing start")

    fix_mdb()
    fix_assets()

    print("Postprocessing done")


def main():
    # do_postprocess()

    a = "012345678901234"
    b = util.get_text_width(a, FONT)
    print(b)
    # d = scale_to_box(a, 15800, 2)
    # print(d)


if __name__ == "__main__":
    main()
