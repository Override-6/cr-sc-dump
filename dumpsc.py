#!/usr/misc/env python3

import argparse
import logging
import os

from processing.csv import process_csv
from processing.ktx import process_ktx
from processing.sc import process_sc
from processing.sctx import process_sctx


def check_header(data):
    if data[0] == 0x5D:
        return "csv"
    if data[:2] == b"\x53\x43":
        return "sc"
    if data[:4] == b"\x53\x69\x67\x3a":
        return "sig:"
    if data[:5] == b"\xab\x4b\x54\x58\x20":
        return "ktx"
    if data[8:12] == b"SCTX":
        return "sctx"
    raise Exception("  Unknown header")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract png files from SC/CSV files")
    parser.add_argument("files", help="sc file", nargs="+")
    parser.add_argument("--old", action="store_true", help="used for '*_dl.sc' files")
    parser.add_argument("-o", help="Extract pngs to directory", type=str)
    parser.add_argument("--verbose", action="store_true", help="Print debug infos")
    parser.add_argument("--fail-fast", action="store_true", help="Do not continue if any error occurs during decoding")
    args = parser.parse_args()

    if args.o:
        path = os.path.normpath(args.o)
    else:
        path = os.getcwd()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(format="", level=level)
    fail_fast = args.fail_fast

    for file in args.files:
        try:
            base_dir = os.path.dirname(file)
            base_name, ext = os.path.splitext(os.path.basename(file))
            logging.info(base_name + ext)
            with open(file, "rb") as f:
                data = f.read()

            file_type = check_header(data)

            if file_type == "csv":
                process_csv(base_name + ext, data, path)
            elif file_type == "sig:":
                process_csv(base_name + ext, data[68:], path)
            elif file_type == "sc":
                process_sc(base_dir, base_name, data, path, args.old)
            elif file_type == "ktx":
                process_ktx(base_name, data, path)
            elif file_type == "sctx":
                process_sctx(base_name, data, path)
        except Exception as e:
            if fail_fast:
                raise e
            logging.error(e)
