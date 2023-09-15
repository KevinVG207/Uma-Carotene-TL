import util
import os
import unicodedata

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

def main():
    # autofill_birthdays()
    pass

if __name__ == "__main__":
    main()
