import util
import glob
import tqdm

def main():
    progress_bar = tqdm.tqdm(total=100, desc="Filling duplicates", position=0, leave=True)

    # all_mdb_jsons = glob.glob(util.MDB_FOLDER_EDITING + "text_data\\*.json", recursive=True)
    files = [
        "29",
        "32",
        "36",
        "38",
        "111",
        "147"
    ]
    all_mdb_jsons = [util.MDB_FOLDER_EDITING + f"text_data\\{file}.json" for file in files]

    hash_dict = {}
    all_dict = {}

    duplicate_files = set()

    progress_per_file = 50 / len(all_mdb_jsons)

    for json_path in all_mdb_jsons:
        entries = util.load_json(json_path)

        for entry in entries:
            cur_hash = entry["hash"]
            if entry["text"] and (cur_hash not in hash_dict or entry["text"] != entry["prev_text"]):
                # Prioritize changed text over unchanged text
                hash_dict[cur_hash] = entry["text"]
            
            if cur_hash not in all_dict:
                all_dict[cur_hash] = []
            all_dict[cur_hash].append(json_path)
        
        progress_bar.update(progress_per_file)
    
    duplicate_hashes = set(hash_dict.keys()).intersection(set(all_dict.keys()))

    for cur_hash in duplicate_hashes:
        if len(all_dict[cur_hash]) > 1:
            duplicate_files.update(all_dict[cur_hash])

    if not duplicate_files:
        progress_bar.close()
        return

    progress_per_file = 50 / len(duplicate_files)

    for json_path in duplicate_files:
        entries = util.load_json(json_path)

        for entry in entries:
            if entry["hash"] in hash_dict:
                entry["text"] = hash_dict[entry["hash"]]
        
        util.save_json(json_path, entries)
        progress_bar.update(progress_per_file)
    
    progress_bar.close()

    print("Updated files:")
    print("\n".join(duplicate_files))



if __name__ == "__main__":
    main()
