import argparse
import configparser
import os
import sys

try:
    from .__version__ import __version__
except ImportError:
    __version__ = "0.0.0"


def parse():
    def is_valid_string_or_file(arg):
        if os.path.isfile(arg):
            return arg
        elif isinstance(arg, str) or arg == "":
            return arg
        else:
            raise argparse.ArgumentTypeError(f"Invalid value: {arg}")

    parser = argparse.ArgumentParser(
        prog="mpgrep",
        description="Download CIF files or XYZ supercells from Materials Project using the new REST API.",
    )
    parser.add_argument(
        "input",
        type=is_valid_string_or_file,
        help="The Materials Project compound ID (e.g., 'mp-149') or the path to a file containing a list of IDs.",
        nargs="?",
        default=None,
    )
    parser.add_argument(
        "-p", dest="primitive", action="store_true", help="Outputs the primitive cell."
    )
    parser.add_argument("--key", type=str, help="Stores your API key.")
    parser.add_argument(
        "--supercell",
        type=int,
        nargs=3,
        metavar=("NX", "NY", "NZ"),
        help="Supercell size along each axis; triggers XYZ output (e.g., --supercell 2 2 2).",
    )
    return parser.parse_args()


def entry_point():
    # Parse cml args
    args = parse()

    from mp_api.client import MPRester
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    from pymatgen.io.cif import CifWriter
    from pymatgen.io.xyz import XYZ

    # Setup the configuration
    config = configparser.ConfigParser()

    # Try to read the config file in the home dir
    rcpath = os.path.expanduser("~/.mpgreprc")
    if not os.path.isfile(rcpath):
        if args.key:
            config["API"] = {"key": args.key}

            # If the file does not exist create a new one and exit
            with open(rcpath, "w") as f:
                config.write(f)

            print("API key stored.")
        else:
            print("Please configure your Materials Project API access.")
            sys.exit(0)
    else:
        # Read the existing config file
        config.read(rcpath)

        # If value in config file is empty (like if the user didn't modify it) exit
        if config["API"]["key"] == "":
            print("Please configure your Materials Project API access.")
            sys.exit(0)

    if not args.input:
        print(
            "Please provide an input (either a Materials Project ID or a file containing ID(s)."
        )
        sys.exit(0)

    # Connect to the MP API
    with MPRester(config["API"]["key"]) as mpr:
        # If a file was given as input try to read all the IDs from that file
        if os.path.isfile(args.input):
            with open(args.input, "r") as f:
                lines = f.readlines()

            ids = [line.strip() for line in lines]
        else:
            # Assume a single ID was given as input
            ids = [args.input]

        # Fetch all structures
        data = mpr.materials.search(
            material_ids=ids, fields=["structure", "material_id"]
        )

        # Print structures which could not be found
        for id in ids:
            if id not in [data_point.material_id for data_point in data]:
                print(f"Could not find structure with ID {id}.")

        for data_point in data:
            sga = SpacegroupAnalyzer(data_point.structure)

            # Get standard cell based on primitive flag
            if args.primitive:
                sym_structure = sga.get_primitive_standard_structure()
            else:
                sym_structure = sga.get_conventional_standard_structure()

            # If supercell requested, output XYZ with supercell
            if args.supercell:
                nx, ny, nz = args.supercell
                if nx != 1 or ny != 1 or nz != 1:
                    sym_structure.make_supercell([[nx, 0, 0], [0, ny, 0], [0, 0, nz]])
                print(f"Writing {data_point.material_id}.xyz ...")
                XYZ(sym_structure).write_file(f"{data_point.material_id}.xyz")
            else:
                # Write CIF file
                print(f"Writing {data_point.material_id}.cif ...")
                if args.primitive:
                    sym_structure.to(filename=f"{data_point.material_id}.cif")
                else:
                    CifWriter(struct=sym_structure, symprec=1e-5).write_file(
                        f"{data_point.material_id}.cif"
                    )
