import os

from util import decompress


def process_csv(file_name, data, path):
    decompressed = decompress(data)
    with open(os.path.join(path, file_name), "wb") as f:
        f.write(decompressed)

