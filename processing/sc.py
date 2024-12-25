import hashlib
import logging
import os

from processing.ktx import process_ktx
from processing.sctx import process_sctx
from reader import Reader
from util import decompress, pixel_size, create_image


def process_file_type_47(file_path, path):
    base_name = os.path.basename(file_path)
    logging.info(f"{base_name}")
    with open(file_path, "rb") as f:
        data = f.read()
    return process_sctx(os.path.splitext(base_name)[0], data, path)


def process_sc(base_dir, base_name, data, path, old):
    reader = Reader(data)
    reader.read(2)
    file_ver_major = reader.read_uint32(byteorder="big")
    file_ver_minor = reader.read_uint32(byteorder="big")
    hash_length = reader.read_uint32(byteorder="big")
    logging.debug(f"sc file version: {file_ver_major}.{file_ver_minor}")
    md5_hash = reader.read(hash_length)
    logging.debug(f"md5 hash: {md5_hash.hex()}")

    decompressed = decompress(reader.read())

    with open(f"output/{base_name}", "wb") as f:
        f.write(decompressed)

    if hashlib.md5(decompressed).digest() != md5_hash:
        logging.debug("File seems corrupted")

    reader = Reader(decompressed)

    if old:
        # Credits: https://github.com/Galaxy1036/Old-Sc-Dumper
        reader.read(17)
        count = reader.read_uint16()
        reader.read(count * 2)
        for i in range(count):  # skip strings
            reader.read_string()

    count = 0
    while len(reader):
        file_type = reader.read_byte()
        file_size = reader.read_uint32()

        start_pos = reader.pos()
        logging.debug(f"decoding sc file {base_name}: sub file type {file_type} (size: {file_size}, global content pos: {start_pos})")
        decode_sc_sub_file(reader, file_type, file_size, base_dir, base_name, path, count)

        expected_pos = start_pos + file_size

        # do not check for type 45 as the given file size does not seems to respect the declared size definition anyway
        assert file_type == 45 or expected_pos == reader.pos(), f"reader misaligned ! expected to be at {expected_pos}, but reader cursor is at {reader.pos()}"
        count += 1


def decode_sc_sub_file(reader, file_type, file_size, base_dir, base_name, path, file_id):
    if file_size == 0:
        return

    elif file_type == 8:
        matrix = [reader.read_int32() for _ in range(6)]
        return

    elif file_type == 12 or file_type == 49:
        data = reader.read(file_size)
        return

    elif file_type == 45:
        file_size = reader.read_uint32()

    elif file_type == 47:
        file_name = reader.read_string()

    elif file_type in [1, 24, 27, 28]:
        pass
    else:
        logging.error(f"Unknown file_type: {file_type} in file {base_name}")
        data = reader.read(file_size)
        return

    sub_type = reader.read_byte()
    width = reader.read_uint16()
    height = reader.read_uint16()

    logging.info(
        f"file_type: {file_type}, file_size: {file_size}, "
        f"sub_type: {sub_type}, width: {width}, height: {height}"
    )

    img = None
    if file_type == 27 or file_type == 28:
        pixel_sz = pixel_size(sub_type)
        block_sz = 32
        pixels = bytearray(file_size - 5)
        for _h in range(0, height, block_sz):
            for _w in range(0, width, block_sz):
                for h in range(_h, min(_h + block_sz, height)):
                    i = (_w + h * width) * pixel_sz
                    sz = min(block_sz, width - _w) * pixel_sz
                    pixels[i: i + sz] = reader.read(sz)
        pixels = bytes(pixels)
        img = create_image(width, height, pixels, sub_type)
    elif file_type == 45:
        process_ktx(base_name, reader.read(), path)
        return
    elif file_type == 47:
        process_file_type_47(os.path.join(base_dir, file_name), path)
        return
    else:
        pixels = reader.read(file_size - 5)
        img = create_image(width, height, pixels, sub_type)

    img.save(os.path.join(path, f"{base_name}_{file_id}.png"))
