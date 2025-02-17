import polib
import pathlib

root = pathlib.Path(__file__).absolute().parent / 'psychopy/app/locale'

def compilePoFiles(root=root, errIfEmpty=True):
    """Looks for all paths matching **/*.po and compiles to a .mo file using
    python polib

    :param: root
    """
    po_files = list(pathlib.Path(root).glob('**/*.po'))

    for popath in po_files:
        mopath = popath.with_suffix(".mo")
        po = polib.pofile(popath)
        po.save_as_mofile(mopath)
    if len(po_files)<1:
        if root.exists():
            raise FileNotFoundError(
                f"Found no po files to compile to mo. Was this the right folder to search? \n"
                f"  {root}"
            )
        else:
            # if app folder doesn't exist, there's nothing to translate
            print("No .po files to compile as this is a library-only installation.")
    else:
        print(f"compiled {len(po_files)} .po files to .mo in {root.absolute()}")
    return len(po_files)

if __name__ in ("__main__", "_local"):
    n_files = compilePoFiles(root)
