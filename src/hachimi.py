import util
import os
import sys
import glob
import pyhash


os.makedirs("hachimi", exist_ok=True)

def convert_tags(text):
    return text \
        .replace("<nb>", "$(nb)") \
        .replace("<a7>", "$(anchor 1)") \
        .replace("<a8>", "$(anchor 2)") \
        .replace("<a9>", "$(anchor 3)") \
        .replace("<a4>", "$(anchor 4)") \
        .replace("<a5>", "$(anchor 5)") \
        .replace("<a6>", "$(anchor 6)") \
        .replace("<a1>", "$(anchor 7)") \
        .replace("<a2>", "$(anchor 8)") \
        .replace("<a3>", "$(anchor 9)")

def convert_jpdict():
    in_path = os.path.join(util.ASSEMBLY_FOLDER, "JPDict.json")
    out_path = os.path.join("hachimi", "localize_dict.json")

    data = util.load_json(in_path)

    out_dict = {}
    for key, entry in data.items():
        if not entry["text"]:
            continue
        
        out_dict[key] = convert_tags(entry["text"])
    
    util.save_json(out_path, out_dict)

def convert_hashed():
    in_path = os.path.join(util.ASSEMBLY_FOLDER_EDITING, "hashed.json")
    out_path = os.path.join("hachimi", "hashed_dict.json")

    data = util.load_json(in_path)

    out_dict = {}
    for entry in data:
        if not entry["text"]:
            return
        
        if not entry["source"]:
            return
        
        source_hash = make_hash(entry["source"])
        
        out_dict[source_hash] = convert_tags(entry["text"])
    
    util.save_json(out_path, out_dict)


def convert_assembly():
    convert_jpdict()
    convert_hashed()

def convert_text_data():
    in_paths = glob.glob(os.path.join(util.MDB_FOLDER, "text_data\\*.json"))
    out_path = os.path.join("hachimi", "text_data_dict.json")

    out_dict = {}

    for in_path in in_paths:
        data = util.load_json(in_path)
        category_key = os.path.basename(in_path).replace(".json", "")
        out_dict[category_key] = {}

        for key, entry in data.items():
            if not entry["text"]:
                continue
            
            out_dict[category_key][key] = convert_tags(entry["text"])

    util.save_json(out_path, out_dict)

def convert_mdb():
    convert_text_data()

def make_hash(text):
    o = 14695981039346656037
    for c in text.encode("utf_16_le"):
        o ^= c
        o *= 1099511628211
        o &= 18446744073709551615
    return o

def main():
    convert_assembly()
    convert_mdb()

if __name__ == "__main__":
    main()
