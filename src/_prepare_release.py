import intermediate
import preprocess

def main():
    preprocess.main()
    intermediate.mdb_from_intermediate()
    intermediate.assets_from_intermediate()

if __name__ == "__main__":
    main()