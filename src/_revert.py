import util
import glob
import shutil
import os

def revert_mdb():
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

def revert_assets():
    asset_backups = glob.glob(util.DATA_PATH + "\\**\\*.bak", recursive=True)
    print(len(asset_backups))
    for asset_backup in asset_backups:
        asset_path = asset_backup.rsplit(".", 1)[0]
        if not os.path.exists(asset_path):
            print(f"Deleting {asset_backup}")
            os.remove(asset_backup)
        else:
            print(f"Reverting {asset_path}")
            shutil.copy(asset_backup, asset_path)
            os.remove(asset_backup)


def main():
    revert_mdb()
    revert_assets()

if __name__ == "__main__":
    main()
