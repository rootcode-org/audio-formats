# Copyright is waived. No warranty is provided. Unrestricted use and modification is permitted.

import io
import hashlib
from streams import ByteStream, FileStream


class WAV:
    def __init__(self):
        self.file_path = None
        self.audio_format = None
        self.num_channels = 0
        self.sample_rate = 0
        self.byte_rate = 0
        self.block_align = 0
        self.bits_per_sample = 0
        self.data = None
        self.data_hash = None
        self.length_in_milliseconds = 0
        self.extension_size = 0
        self.valid_bits_per_sample = 0
        self.channel_mask = 0
        self.sub_format = None

    def load(self, file_path):
        self.file_path = file_path
        stream = FileStream(self.file_path, 'rb')

        # Read header
        chunk_id = stream.read_u32()
        chunk_size = stream.read_u32()
        chunk_format = stream.read_u32()

        # Read all chunks
        file_size = chunk_size + 8
        while stream.get_position() < (file_size - 3):
            sub_chunk_id = stream.read_u32()
            sub_chunk_size = stream.read_u32()
            if sub_chunk_id == 0x20746d66:      # 'fmt '
                self.audio_format = stream.read_u16()
                self.num_channels = stream.read_u16()
                self.sample_rate = stream.read_u32()
                self.byte_rate = stream.read_u32()
                self.block_align = stream.read_u16()
                self.bits_per_sample = stream.read_u16()
                if sub_chunk_size > 16:
                    self.extension_size = stream.read_u16()
                    if sub_chunk_size == 40:
                        self.valid_bits_per_sample = stream.read_u16()
                        self.channel_mask = stream.read_u32()
                        self.sub_format = stream.read_u8_array(16)
            elif sub_chunk_id == 0x61746164:    # 'data'
                self.data = stream.read_u8_array(sub_chunk_size)
                self.length_in_milliseconds = (len(self.data) * 1000) / self.byte_rate
            else:
                stream.set_position(sub_chunk_size, io.SEEK_CUR)
        stream.close()

    def save(self):
        total_size = 4                              # 'WAVE' identifier
        total_size += 8 + 16                        # 'fmt ' chunk
        total_size += 8 + len(self.data)            # 'data' chunk

        stream = ByteStream()
        stream.write_u32(0x46464952)           # 'RIFF'
        stream.write_u32(total_size)
        stream.write_u32(0x45564157)           # 'WAVE'

        stream.write_u32(0x20746d66)           # 'fmt '
        stream.write_u32(16)
        stream.write_u16(self.audio_format)
        stream.write_u16(self.num_channels)
        stream.write_u32(self.sample_rate)
        stream.write_u32(self.byte_rate)
        stream.write_u16(self.block_align)
        stream.write_u16(self.bits_per_sample)

        stream.write_u32(0x61746164)           # 'data'
        stream.write_u32(len(self.data))
        stream.write_u8_array(self.data)

        with open(self.file_path, 'wb') as f:
            f.write(stream.get_data())

    def get_sample_rate(self):
        return self.sample_rate

    def get_num_channels(self):
        return self.num_channels

    def get_bits_per_sample(self):
        return self.bits_per_sample

    def get_length_in_milliseconds(self):
        return self.length_in_milliseconds

    def get_data_hash(self):
        if self.data_hash is None:
            self.data_hash = bytearray(hashlib.sha1(self.data).digest())
        return self.data_hash
