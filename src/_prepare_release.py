import intermediate
import _fill_duplicates

def main():
    _fill_duplicates.main()
    intermediate.mdb_from_intermediate()
    intermediate.assets_from_intermediate()

if __name__ == "__main__":
    main()