import intermediate
# import _fill_duplicates
import autofill_mdb
import autofill_assets
import _unpatch
import postprocess
import hachimi

def main():
    _unpatch.main()
    # _fill_duplicates.main()
    autofill_mdb.run()
    autofill_assets.run()
    intermediate.mdb_from_intermediate()
    intermediate.assets_from_intermediate()
    intermediate.assembly_from_intermediate()
    postprocess.do_postprocess()
    hachimi.convert()

if __name__ == "__main__":
    main()
