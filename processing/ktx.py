import logging
import os

import texture2ddecoder
from PIL import Image

from reader import Reader


def process_ktx(base_name, data, path):
    reader = Reader(data)

    identifier = reader.read(12)
    if b"KTX 11" in identifier:
        image_data, height, width, file_type = process_ktx11(reader)
    elif b"KTX 20" in identifier:
        image_data, height, width, file_type = process_ktx20(reader)
    else:
        raise Exception(f"Unknown KTX identifier '{identifier}'")

    logging.info(
        f"ktx file_type: {file_type}, width: {width}, height: {height}"
    )
    if file_type == 157:  # VK_FORMAT_ASTC_4x4_UNORM_BLOCK
        pixels = texture2ddecoder.decode_astc(
            image_data,
            width,
            height,
            4,
            4,
        )
    elif file_type == 165:  # VK_FORMAT_ASTC_6x6_UNORM_BLOCK
        pixels = texture2ddecoder.decode_astc(
            image_data,
            width,
            height,
            6,
            6,
        )
    elif file_type in [171, 172]:  # VK_FORMAT_ASTC_8x8_UNORM_BLOCK
        pixels = texture2ddecoder.decode_astc(
            image_data,
            width,
            height,
            8,
            8,
        )
    elif file_type == 0x8D64:  # ETC1_RGB8_OES
        pixels = texture2ddecoder.decode_etc1(image_data, width, height)
    elif file_type == 0x93B0:  # COMPRESSED_RGBA_ASTC_4x4_KHR
        pixels = texture2ddecoder.decode_astc(
            image_data,
            width,
            height,
            4,
            4,
        )
    elif file_type == 0x93B4:  # COMPRESSED_RGBA_ASTC_6x6_KHR
        pixels = texture2ddecoder.decode_astc(
            image_data,
            width,
            height,
            6,
            6,
        )
    else:
        raise Exception(f"Unknown file type '{file_type}'")

    img = Image.frombytes("RGBA", (width, height), pixels, "raw", "BGRA")
    img.save(os.path.join(path, f"{base_name}.png"))


class KhronosTexture11():
    self.test: int

# khronos texture format 1.0, see https://registry.khronos.org/KTX/specs/1.0/ktxspec.v1.html
def process_ktx11(reader):
    identifier = reader.read(16)
    gl_internal_format = reader.read_uint32()
    gl_base_internal_format = reader.read_uint32()
    pixel_width = reader.read_uint32()
    pixel_height = reader.read_uint32()
    reader.read(16)

    reader.read(reader.read_uint32())
    reader.read(4)
    return reader.read(), pixel_height, pixel_width, gl_internal_format

# Khronos texture file format 2.0, see https://registry.khronos.org/KTX/specs/2.0/ktxspec.v2.html
def process_ktx20(reader):
    vk_format = reader.read_uint32()
    reader.read(4)
    pixel_width = reader.read_uint32()
    pixel_height = reader.read_uint32()
    reader.read(12)
    level_count = reader.read_uint32()
    reader.read(4)
    # index
    reader.read(8)
    kvd_byte_offset = reader.read_uint32()
    kvd_byte_length = reader.read_uint32()
    reader.read(4)
    sgd_byte_length = reader.read_uint32()
    reader.read(8)
    # level index
    for _ in range(max(1, level_count)):
        reader.read(24)
    reader.read(reader.read_uint32() - 4)
    while reader._bytes_read < kvd_byte_offset + kvd_byte_length:
        key_and_value = reader.read(reader.read_uint32())
        logging.debug(key_and_value.replace(b"\0", b" ").decode("ascii"))
        reader.align_to(4)
    reader.align_to(16)
    reader.read(sgd_byte_length)
    return reader.read(), pixel_height, pixel_width, vk_format
