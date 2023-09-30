import index
import _revert

def main():
    _revert.main()
    index.index_mdb()
    index.index_assets()
    index.index_assembly()

if __name__ == "__main__":
    main()
