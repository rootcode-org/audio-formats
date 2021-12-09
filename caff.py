# Copyright is waived. No warranty is provided. Unrestricted use and modification is permitted.

import io
from streams import FileStream


class CAFF:
    def __init__(self):
        self.file_path = None
        self.sample_rate = 0
        self.audio_format = None
        self.format_flags = 0
        self.bytes_per_packet = 0
        self.frames_per_packet = 0
        self.num_channels = 0
        self.bits_per_channel = 0
        self.packet_table = None
        self.info_map = {}
        self.free_size = 0
        self.source_hash = None
        self.data = None

    def load(self, file_path):
        self.file_path = file_path
        stream = FileStream(self.file_path, 'rb', FileStream.BIG_ENDIAN)
        file_type = stream.read_u32()
        file_version = stream.read_u16()
        file_flags = stream.read_u16()

        while not stream.is_eof():
            chunk_type = stream.read_u32()
            chunk_size = stream.read_u64()

            if chunk_type == 0x64657363:         # 'desc'
                self.sample_rate = stream.read_f64()
                self.audio_format = stream.read_string(4)
                self.format_flags = stream.read_u32()
                self.bytes_per_packet = stream.read_u32()
                self.frames_per_packet = stream.read_u32()
                self.num_channels = stream.read_u32()
                self.bits_per_channel = stream.read_u32()

            elif chunk_type == 0x696e666f:            # 'info'
                num_entries = stream.read_u32()
                for i in range(num_entries):
                    key = stream.read_nt_string()
                    value = stream.read_nt_string()
                    self.info_map[key] = value

            elif chunk_type == 0x70616B74:              # 'pakt'
                self.packet_table = stream.read_u8_array(chunk_size)

            elif chunk_type == 0x66726565:              # 'free'
                self.free_size = chunk_size
                stream.set_position(chunk_size, io.SEEK_CUR)

            elif chunk_type == 0x68617368:              # 'hash'
                self.source_hash = stream.read_u8_array(chunk_size)

            elif chunk_type == 0x64617461:               # 'data'
                self.data = stream.read_u8_array(chunk_size)
            else:
                print ('WARNING: Unknown chunk type ' + hex(chunk_type))
                stream.set_position(chunk_size, io.SEEK_CUR)
        stream.close()

    def get_format(self):
        return self.audio_format

    def get_sample_rate(self):
        return self.sample_rate

    def get_num_channels(self):
        return self.num_channels

    def get_source_hash(self):
        return self.source_hash

