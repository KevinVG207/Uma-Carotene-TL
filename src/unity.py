import os
import UnityPy
import util
import shutil

def load_assetbundle(path, hash):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path {path} does not exist. Cannot load assetbundle.")
    asset = UnityPy.load(path)

    try:
        root = list(asset.container.values())[0].get_obj()
    except IndexError:
        root = None
    
    if root is None:
        # Maybe the asset is corrupted.
        # We try downloading it again.
        util.download_asset(hash, no_progress=True)
        shutil.copy(path, path + ".bak")
        asset = UnityPy.load(path)
        try:
            root = list(asset.container.values())[0].get_obj()
        except IndexError:
            root = None

    return root

def load_asset(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path {path} does not exist. Cannot load asset.")
    asset = UnityPy.load(path)

    return asset