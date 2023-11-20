import json
import os
import time
from multiprocessing import Pool
import util
import glob
import hashlib


FILES_TO_IMPORT = [
    "race-tracks",
    "race-name",
    "uma-profile-shoesize",
    "uma-profile-weight",
    "uma-profile-tagline",
    "uma-profile-intro",
    "uma-profile-strengths",
    "uma-profile-weaknesses",
    "uma-profile-ears",
    "uma-profile-tail",
    "uma-profile-family"
]


def get_table(table, columns, dest):
    with util.MDBConnection() as (_, cursor):
        cursor.execute(
            f"""SELECT {columns}, {dest} FROM {table}"""
        )
        rows = cursor.fetchall()
    
    if not rows:
        return {}
    
    data_dict = {}

    def add_to_dict(parent_dict, values_list):
        if len(values_list) == 2:
            parent_dict[values_list[0]] = values_list[1]
        else:
            if values_list[0] not in parent_dict:
                parent_dict[values_list[0]] = {}
            add_to_dict(parent_dict[values_list[0]], values_list[1:])
    
    for row in rows:
        add_to_dict(data_dict, row)
    
    return data_dict


def main():
    config = util.load_json("src/config.json")
    dl_base = config.get("source", None)

    if not dl_base:
        raise ValueError("No download base specified in config with key 'source'")
    
    if dl_base.endswith("/"):
        dl_base = dl_base[:-1]

    index_url = dl_base + "/src/mdb/index.json"
    
    dl_base = dl_base + "/translations/mdb/"

    # Create TL folder
    os.makedirs("translations/mdb", exist_ok=True)

    # Download index
    index = util.download_json(index_url + f"?nocache={int(time.time())}""")

    for table in index:
        if 'file' in table:
            table['files'] = {table['file']: None}

        if table['table'] == "character_system_text":
            table['files'] = {"character_system_text/" + file: metadata for file, metadata in table['files'].items()}

        pool_before = time.perf_counter()
        with Pool(processes=min(os.cpu_count(), 16)) as pool:
            result = pool.map(util.download_json, [dl_base + file + ".json" for file in table['files'].keys()])
            file_jsons = {file: json for file, json in zip(table['files'].keys(), result)}
        pool_after = time.perf_counter()
        print(f"Fetch time: {pool_after - pool_before}")

        for file, metadata in table['files'].items():
            if file not in FILES_TO_IMPORT:
                continue
            
            print(file)

            categories = []

            if not isinstance(metadata, dict):
                if not isinstance(metadata, list):
                    categories.append(metadata)
                else:
                    for category in metadata:
                        if isinstance(category, dict):
                            categories.append(category['spec'])
                        else:
                            categories.append(category)
            else:
                # Data is a dictionary
                category_ids = metadata.get('spec', [])

                if isinstance(category_ids, int):
                    category_ids = [category_ids]

                for category_id in category_ids:
                    categories.append(category_id)
            
            print(categories)

            # Prepare the data
            file_json = file_jsons[file]
            trans_dict = {hashlib.sha256(jp_text.encode("utf-8")).hexdigest(): en_text for jp_text, en_text in file_json['text'].items() if en_text}

            # Determine file to open
            files_to_open = []
            for id in categories:
                if id is not None and table['table'] in ("text_data", "character_system_text"):
                    files_to_open.append(os.path.join(util.MDB_FOLDER_EDITING, table['table'], str(id) + ".json"))
                elif id is None and table['table'] == "text_data":
                    check_path = os.path.join(util.MDB_FOLDER_EDITING, table['table'] + "/**/*.json")
                    files_to_open += glob.glob(check_path, recursive=True)
                else:
                    files_to_open.append(os.path.join(util.MDB_FOLDER_EDITING, table['table'] + ".json"))
            
            # Open the files
            for file_to_open in files_to_open:
                with open(file_to_open, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                for tl_item in file_data:
                    if tl_item['hash'] in trans_dict and not tl_item['text']:
                        tl_item['text'] = trans_dict[tl_item['hash']]
                        tl_item['new'] = False
                
                with open(file_to_open, "w", encoding="utf-8") as f:
                    f.write(util.json.dumps(file_data, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
