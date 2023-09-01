import util
import glob
import shutil
import os

def main():
    backup_files = glob.glob(util.MDB_PATH + ".*")
    if len(backup_files) == 0:
        raise FileNotFoundError(f"No backup files found for MDB: {util.MDB_PATH}")
    
    time_dict = {int(path.rsplit(".", 1)[1]): path for path in backup_files}

    latest_time = max(time_dict.keys())
    latest_backup = time_dict[latest_time]

    print(f"Reverting to backup: {latest_backup}")
    shutil.copy(latest_backup, util.MDB_PATH)

    for backup_file in backup_files:
        if backup_file != latest_backup:
            os.remove(backup_file)

if __name__ == "__main__":
    main()
