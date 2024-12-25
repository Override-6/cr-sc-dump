import io


class Reader(io.BytesIO):
    def __init__(self, stream):
        super().__init__(stream)
        self._bytes_left = len(stream)
        self._bytes_read = 0

    def __len__(self):
        return 0 if self._bytes_left < 0 else self._bytes_left

    def align_to(self, alignment):
        remainder = alignment - (self._bytes_read % alignment)
        self.read(remainder if remainder != alignment else 0)

    def pos(self):
        return self._bytes_read

    def read(self, size=-1):
        if size == -1:
            self._bytes_read += self._bytes_left
            self._bytes_left = 0
        else:
            self._bytes_left -= size
            self._bytes_read += size
        return super().read(size)

    def read_byte(self, byteorder="little"):
        return int.from_bytes(self.read(1), byteorder)

    def read_uint16(self, byteorder="little"):
        return int.from_bytes(self.read(2), byteorder)

    def read_int32(self, byteorder="little"):
        return int.from_bytes(self.read(4), byteorder, signed=True)

    def read_uint32(self, byteorder="little"):
        return int.from_bytes(self.read(4), byteorder)

    def read_uint64(self, byteorder="little"):
        return int.from_bytes(self.read(8), byteorder)

    def read_string(self, encoding="utf-8"):
        length = self.read_byte()
        return self.read(length).decode("utf-8")

