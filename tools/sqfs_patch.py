"""Patch PySquashfsImage LZ4 to use raw block format (squashfs uses lz4 block, not frame)."""
import lz4.block
from PySquashfsImage import compressor


class LZ4BlockCompressor(compressor.Compressor):
    name = "lz4"

    def __init__(self):
        pass

    def uncompress(self, src, size, outsize):
        return lz4.block.decompress(src, uncompressed_size=outsize)


compressor.compressors[compressor.Compression.LZ4] = LZ4BlockCompressor
