import util
import os

titles = {
    "三冠ウマ娘": "Triple Crown winner",
    "秋の三冠ウマ娘": "Autumn Triple Crown winner",
    "トリプルティアラのウマ娘": "Triple Tiara winner",
    "春の三冠ウマ娘": "Spring Triple Crown winner",
    "二冠ウマ娘": "Double Crown winner",
    "2大マイル戦覇者": "2 Major Mile champion",
    "2大スプリント覇者": "2 Major Sprint champion",
    "2大ダート戦覇者": "2 Major Dirt champion",
    "グランプリウマ娘": "Grand Prix champion",
    "ダービーウマ娘": "Derby champion",
    "天皇賞ウマ娘": "Tenno Sho champion",
    "皐月賞ウマ娘": "Satsuki Sho champion",
    "菊花賞ウマ娘": "Kikka Sho champion",
    "オークスウマ娘": "Oaks champion",
    "桜花賞ウマ娘": "Oka Sho champion",
    "秋華賞ウマ娘": "Shuka Sho champion",
    "ジュニア王者": "Junior champion",
    "春の天皇賞ウマ娘": "Spring Tenno Sho champion",
    "前年の覇者": "last year's champion",
    "ニエル賞を制した": "Prix Niel winner",
    "フォワ賞を制した": "Prix Foy winner",

    "ここまで無敗三冠ウマ娘": "undefeated Triple Crown winner",
    "ここまで無敗秋の三冠ウマ娘": "undefeated Autumn Triple Crown winner",
    "ここまで無敗トリプルティアラのウマ娘": "undefeated Triple Tiara winner",
    "ここまで無敗春の三冠ウマ娘": "undefeated Spring Triple Crown winner",
    "ここまで無敗二冠ウマ娘": "undefeated Double Crown winner",
    "ここまで無敗2大マイル戦覇者": "undefeated 2 Major Mile champion",
    "ここまで無敗2大スプリント覇者": "undefeated 2 Major Sprint champion",
    "ここまで無敗2大ダート戦覇者": "undefeated 2 Major Dirt champion",
    "ここまで無敗グランプリウマ娘": "undefeated Grand Prix champion",
    "ここまで無敗ダービーウマ娘": "undefeated Derby champion",
    "ここまで無敗天皇賞ウマ娘": "undefeated Tenno Sho champion",
    "ここまで無敗皐月賞ウマ娘": "undefeated Satsuki Sho champion",
    "ここまで無敗菊花賞ウマ娘": "undefeated Kikka Sho champion",
    "ここまで無敗オークスウマ娘": "undefeated Oaks champion",
    "ここまで無敗桜花賞ウマ娘": "undefeated Oka Sho champion",
    "ここまで無敗秋華賞ウマ娘": "undefeated Shuka Sho champion",
    "ここまで無敗ジュニア王者": "undefeated Junior champion",
    "ここまで無敗春の天皇賞ウマ娘": "undefeated Spring Tenno Sho champion",
    "ここまで無敗前年の覇者": "last year's undefeated champion",
    "ここまで無敗ニエル賞を制した": "undefeated Prix Niel winner",
    "ここまで無敗フォワ賞を制した": "undefeated Prix Foy winner",
}

def extract_templates():
    mdb_path = os.path.join(util.MDB_FOLDER_EDITING, "race_jikkyo_message.json")
    message_list = util.load_json(mdb_path)

    out_path = "jikkyo_templates.json"
    if os.path.exists(out_path):
        print("Output file already exists. Exiting.")
        return
    
    out = []

    for message in message_list:
        source = message["source"]
        text = message["text"]

        if not "春の天皇賞ウマ娘" in source:
            continue

        source = source.replace("春の天皇賞ウマ娘", "{}")
        text = text.replace("Spring Tenno Sho champion", "{}")

        out.append((source, text))
    
    util.save_json(out_path, out)

def make_tl_dict():
    templates_path = "jikkyo_templates.json"
    templates = util.load_json(templates_path)

    tl_dict = {}

    for source, text in templates:
        for title_jp, title_en in titles.items():
            key = source.format(title_jp)
            value = text.format(title_en)
            tl_dict[key] = value
    
    return tl_dict

def apply_tl_dict(tl_dict):
    mdb_path = os.path.join(util.MDB_FOLDER_EDITING, "race_jikkyo_message.json")
    message_list = util.load_json(mdb_path)

    for message in message_list:
        source = message["source"]

        if source in tl_dict:
            message["text"] = tl_dict[source]

    util.save_json(mdb_path, message_list)

def main():
    # extract_templates()
    tl_dict = make_tl_dict()
    apply_tl_dict(tl_dict)

if __name__ == "__main__":
    main()
