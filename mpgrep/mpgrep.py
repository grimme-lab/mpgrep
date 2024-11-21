from mp_api.client import MPRester
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.io.cif import CifWriter
import argparse


def parse():
    parser = argparse.ArgumentParser(
        description="Download CIF files from Materials Project using the API."
    )
    parser.add_argument("id", help="The Materials Project compound ID (e.g., 'mp-149')")
    parser.add_argument(
        "-p", dest="primitive", action="store_true", help="Output primitive cell"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse()

    with MPRester("xHFydzd3lHUM0LSA2CEXd8OSvyooGgLI") as mpr:
        structure = mpr.get_structure_by_material_id(args.id)
        sga = SpacegroupAnalyzer(structure)

        if args.primitive:
            sym_structure = sga.get_primitive_standard_structure()
            sym_structure.to(filename=f"{args.id}.cif")
        else:
            sym_structure = sga.get_conventional_standard_structure()
            CifWriter(struct=sym_structure, symprec=1e-5).write_file(f"{args.id}.cif")
