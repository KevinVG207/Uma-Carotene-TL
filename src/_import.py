import util
import os
import glob
import time
import shutil

def backup_mdb():
    print("Backing up MDB...")
    shutil.copy(util.MDB_PATH, util.MDB_PATH + f".{round(time.time())}")

def import_mdb():
    mdb_jsons = glob.glob(util.MDB_FOLDER + "\\**\\*.json")

    with util.MDBConnection() as (conn, cursor):
        for mdb_json in mdb_jsons:
            path_segments = os.path.normpath(mdb_json).rsplit(".", 1)[0].split(os.sep)
            category = path_segments[-1]
            table = path_segments[-2]

            print(f"Importing {table} {category}")
            data = util.load_json(mdb_json)

            for index, entry in data.items():

                cursor.execute(
                    f"""UPDATE {table} SET text = ? WHERE category = ? and `index` = ?;""",
                    (entry['text'], category, index)
                )
        
        conn.commit()
    
    print("Import complete.")


def main():
    if not os.path.exists(util.MDB_PATH):
        raise FileNotFoundError(f"MDB not found: {util.MDB_PATH}")

    backup_mdb()

    import_mdb()

if __name__ == "__main__":
    main()
