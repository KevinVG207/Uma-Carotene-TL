import _patch
import _unpatch
import util
import glob
import os
from multiprocessing import Pool
from tqdm import tqdm
import shutil

def create_diffs():
    # _patch.import_assets()

    # Delete all diffs
    if os.path.exists(util.DIFF_FOLDER):
        shutil.rmtree(util.DIFF_FOLDER)

    # Find all .bak files
    bak_files = glob.glob(util.DATA_PATH + "\\**\\*.bak", recursive=True)

    for bak_file in tqdm(bak_files):
        edited_file = bak_file[:-4]
        source_bytes = util.read_bytes(bak_file)
        edited_bytes = util.read_bytes(edited_file)

        diff = util.make_diff(edited_bytes, source_bytes)

        file_hash = os.path.basename(edited_file)

        out_path = util.DIFF_FOLDER + file_hash
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        util.write_bytes(diff, out_path)


    _unpatch.revert_assets()

def main():
    create_diffs()

if __name__ == "__main__":
    main()