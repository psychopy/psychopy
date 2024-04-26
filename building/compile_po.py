import polib
import pathlib

root = pathlib.Path(__file__).absolute().parent.parent / 'psychopy/app/locale'

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
        raise FileNotFoundError(f"Found no po files to compile to mo. Was this the right folder to search? "
                                f"\n  {root}")
    else:
        print(f"compiled {len(po_files)} .po files to .mo in {root.absolute()}")
    return len(po_files)

if __name__ == "__main__":
    n_files = compilePoFiles(root)