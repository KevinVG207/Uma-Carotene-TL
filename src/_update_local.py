import index
import _unpatch
import hachimi

def main():
    _unpatch.main()
    index.index_mdb()
    index.index_assets()
    index.index_assembly()

if __name__ == "__main__":
    main()
