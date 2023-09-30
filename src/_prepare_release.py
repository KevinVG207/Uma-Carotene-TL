import intermediate
# import _fill_duplicates
import autofill_mdb

def main():
    # _fill_duplicates.main()
    autofill_mdb.main()
    intermediate.mdb_from_intermediate()
    intermediate.assets_from_intermediate()
    intermediate.assembly_from_intermediate()

if __name__ == "__main__":
    main()