import zipfile
import shutil
import os
import src.util as util

VERSION = "v0.0.1"

BUILD_PATH = "dist"

def main():
    os.makedirs(BUILD_PATH, exist_ok=True)
    shutil.make_archive(os.path.join(BUILD_PATH, f"Carotene-TL-{VERSION}"), "zip", util.TL_PREFIX)

if __name__ == "__main__":
    main()
