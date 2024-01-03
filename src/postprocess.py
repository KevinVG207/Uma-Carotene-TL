import math
import util
from tqdm import tqdm


FONT = util.prepare_font()


def add_slogan_tag(text):
    return "<slogan>" + text


def add_scale_tag(text, max_width):
    cur_width = util.get_text_width(text, FONT)
    if cur_width <= max_width:
        return text
    
    scale_factor = math.floor(max_width / cur_width * 100)

    return f"<ssc>{scale_factor}<esc>{text}"


PP_FUNCS = {
    # Slogans
    ("text_data", "144"): (add_slogan_tag, None),
    
    # Support cards
    ("text_data", "76"): (add_scale_tag, (14800,)),

    # Outfits
    ("text_data", "5"): (add_scale_tag, (14800,)),

    # Chara names
    ("text_data", "6"): (add_scale_tag, (9500,)),
    ("text_data", "77"): (add_scale_tag, (9500,)),
    ("text_data", "78"): (add_scale_tag, (9500,)),
    ("text_data", "170"): (add_scale_tag, (9500,)),
}


def fix_mdb():
    for mdb_json_path in tqdm(util.get_tl_mdb_jsons(), desc="Postprocessing MDBs"):
        key = util.split_mdb_path(mdb_json_path)
        data = util.load_json(mdb_json_path)

        for entry in data.values():
            # Clean up any previous processed data
            if 'processed' in entry:
                del entry['processed']

            if not entry.get('text'):
                continue

            if key in PP_FUNCS:
                pp_func, pp_args = PP_FUNCS[key]

                if pp_args:
                    processed = pp_func(entry['text'], *pp_args)
                else:
                    processed = pp_func(entry['text'])
                
                if processed != entry['text']:
                    entry['processed'] = processed
        
        util.save_json(mdb_json_path, data)


def do_postprocess():
    print("Postprocessing start")

    fix_mdb()

    print("Postprocessing done")


def main():
    do_postprocess()

if __name__ == "__main__":
    main()
