import util
import glob
import shutil
import os
import _patch
from settings import settings

def revert_mdb():
    print("Reverting MDB")
    with util.MDBConnection() as (conn, cursor):
        # Restore tables starting with "patch_backup_"
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '{util.TABLE_BACKUP_PREFIX}%';")
        tables = cursor.fetchall()
        if not tables:
            return

        for table in tables:
            table = table[0]
            print(f"Restoring {table}")
            # Copy the backup table to the original table
            cursor.execute(f"SELECT * FROM {table};")
            rows = cursor.fetchall()
            
            normal_table = table[len(util.TABLE_BACKUP_PREFIX):]

            # Check if the table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{normal_table}';")
            if not cursor.fetchall():
                print(f"Table {normal_table} does not exist. Skipping.")
                continue

            # Chunk the rows
            for i in range(0, len(rows), 1000):
                chunk = rows[i:i+1000]
                cursor.executemany(f"INSERT OR REPLACE INTO {normal_table} VALUES ({','.join(['?']*len(chunk[0]))});", chunk)

            # Delete the backup table
            cursor.execute(f"DROP TABLE {table};")

        conn.commit()
        cursor.execute("VACUUM;")
        conn.commit()

def revert_assets():
    asset_backups = glob.glob(util.DATA_PATH + "\\**\\*.bak", recursive=True)
    print(f"Reverting {len(asset_backups)} assets")
    for asset_backup in asset_backups:
        asset_path = asset_backup.rsplit(".", 1)[0]
        if not os.path.exists(asset_path):
            # print(f"Deleting {asset_backup}")
            os.remove(asset_backup)
        else:
            # print(f"Reverting {asset_path}")
            shutil.copy(asset_backup, asset_path)
            os.remove(asset_backup)


def revert_assembly(dl_latest=False):
    print("Reverting translations.txt")
    game_folder = util.get_game_folder()

    if not game_folder:
        print("Game folder could not be determined. Skipping.")
        return

    if not os.path.exists(game_folder):
        print(f"Game folder {game_folder} does not exist. Skipping.")
        return

    translations_path = os.path.join(game_folder, "translations.txt")

    if not os.path.exists(translations_path):
        print("translations.txt does not exist. Skipping.")
    else:
        os.remove(translations_path)

    if settings.cellar_downloaded:
        settings.cellar_downloaded = False
        dxgi_path = os.path.join(game_folder, "dxgi.dll")
        if settings.dxgi_backup:
            print("Restoring previous dxgi.dll")
            dxgi_bak_path = dxgi_path + util.DLL_BACKUP_SUFFIX
            shutil.move(dxgi_bak_path, dxgi_path)
            settings.dxgi_backup = False
        else:
            print("Removing Cellar")
            os.remove(dxgi_path)

    if dl_latest:
        dll_name = settings.dll_name
        if dll_name:
            settings.dll_name = None
            dll_path = os.path.join(game_folder, dll_name)

            if os.path.exists(dll_path):
                print(f"Deleting {dll_name}")
                os.remove(dll_path)

            bak_path = os.path.join(game_folder, dll_path + util.DLL_BACKUP_SUFFIX)
            
            if os.path.exists(bak_path):
                print(f"Restoring previous {dll_name}")
                shutil.move(bak_path, dll_path)
            
            _patch.remove_from_cellar_txt(dll_path, game_folder)
        
        tlg_config_bak = settings.tlg_config_bak
        if tlg_config_bak:
            tlg_config_path = os.path.join(game_folder, tlg_config_bak)
            if os.path.exists(tlg_config_path):
                print(f"Restoring previous {tlg_config_bak}")
                shutil.move(tlg_config_path, tlg_config_path[:-len(util.DLL_BACKUP_SUFFIX)])
            settings.tlg_config_bak = None
        
        tlg_orig_name = settings.tlg_orig_name
        if tlg_orig_name:
            tlg_new_path = os.path.join(game_folder, 'tlg.dll')
            tlg_orig_path = os.path.join(game_folder, tlg_orig_name)

            if os.path.exists(tlg_new_path):
                print(f"Reverting TLG to {tlg_orig_path}")
                shutil.move(tlg_new_path, tlg_orig_path)

            settings.tlg_orig_name = None
        
        cj_orig_name = settings.cj_orig_name
        if cj_orig_name:
            cj_orig_path = os.path.join(game_folder, cj_orig_name)
            cj_bak_path = cj_orig_path + util.DLL_BACKUP_SUFFIX

            if os.path.exists(cj_bak_path):
                print(f"Reverting CarrotJuicer to {cj_orig_path}")
                shutil.move(cj_bak_path, cj_orig_path)

            settings.cj_orig_name = None

    else:
        print(f"Keeping dll")


def main(dl_latest=False):
    print("=== Unpatching ===")
    settings.customization_changed = False

    revert_mdb()
    revert_assets()
    revert_assembly(dl_latest)
    _patch.revert_meta_db()
    _patch.mark_mdb_untranslated()
    settings.install_started = False
    settings.installed_version = None
    settings.dll_version = None
    settings.installed = False
    print("=== Unpatch complete! ===\n")

if __name__ == "__main__":
    main(dl_latest=False)
