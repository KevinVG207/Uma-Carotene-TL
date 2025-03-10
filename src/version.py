# In case more metadata is added in the future, we need to keep track of the version of the intermediate files.

VERSION = (24, 8, 24, 0)

def version_to_string(version):
    return "v" + ".".join(str(v) for v in version)

def string_to_version(version_string):
    if version_string.startswith("v"):
        version_string = version_string[1:]
    
    return tuple(int(v) for v in version_string.split("."))