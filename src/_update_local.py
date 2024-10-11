import index
import _unpatch
import hachimi

def main():
    _unpatch.main()
    hachimi.backport_before()
    index.index_mdb()
    index.index_assets()
    index.index_assembly()
    hachimi.backport_after()

if __name__ == "__main__":
    main()
