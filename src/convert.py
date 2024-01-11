import util
import json
import os

def export_unique_inherited_skills():
    print("Exporting unique inherited skills")
    path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "48.json")
    data = util.load_json(path)

    skill_dict = {}
    for entry in data:
        # Entries in this category should only have one key
        key = str(json.loads(entry["keys"])[0][1])
        skill_dict[key] = (entry["source"], entry["text"])
    
    with open("unique_inherited_skills.csv", "w", encoding="utf-8") as f:
        for key in skill_dict:
            if key.startswith("9"):
                # Is an inherited skill
                unique_id = "1" + key[1:]
                unique_data = skill_dict[unique_id]

                inher_data = skill_dict[key]

                f.write(f"{unique_id},\"{unique_data[0]}\"\n")
                f.write(f"{key},\"{inher_data[0]}\"\n")
                f.write(f"{unique_id},\"{unique_data[1]}\"\n")
                f.write(f"{key},\"{unique_data[1]}\"\n")
                f.write(",\n")

    print("Done")


def import_unique_inherited_skills():
    if not os.path.exists("unique_inherited_skills.csv"):
        print("Error: unique_inherited_skills.csv not found")
        return
    
    inherited_dict = {}

    with open("unique_inherited_skills.csv", "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i in range(0, len(lines), 5):
        tl_line = lines[i+3].strip()
        id, tl = tl_line.split(",", 1)
        if not tl:
            continue
        tl = tl[1:-1]
        inherited_dict[id] = tl
    
    path = os.path.join(util.MDB_FOLDER_EDITING, "text_data", "48.json")
    data = util.load_json(path)

    for entry in data:
        key = str(json.loads(entry["keys"])[0][1])
        if key in inherited_dict:
            entry["prev_text"] = entry["text"]
            entry["text"] = inherited_dict[key]
            entry["new"] = False

    util.save_json(path, data)




def main():
    # export_unique_inherited_skills()
    import_unique_inherited_skills()

if __name__ == "__main__":
    main()
