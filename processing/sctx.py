import logging
import os

import texture2ddecoder
from PIL import Image

from reader import Reader
from util import decompress


def process_sctx(base_name, data, path):
    reader = Reader(data)
    reader.read(52)
    width = reader.read_uint16()
    height = reader.read_uint16()
    file_type = reader.read_uint32()
    length = reader.read_uint32()
    reader.read(16)
    reader.read(reader.read_uint32())
    reader.read(52)
    logging.info(
        f"file_type: {file_type}, file_size: {length}, width: {width}, height: {height}"
    )

    if file_type == 12:
        block_width = block_height = 4
        pixels = reader.read()
    elif file_type == 5:
        pixels = decompress(reader.read())
        block_width = block_height = 8
    else:
        raise Exception(f"Unknown file type '{file_type}'")

    pixels = texture2ddecoder.decode_astc(
        pixels,
        width,
        height,
        block_width,
        block_height,
    )
    img = Image.frombytes("RGBA", (width, height), pixels, "raw", "BGRA")
    img.save(os.path.join(path, f"{base_name}.png"))



