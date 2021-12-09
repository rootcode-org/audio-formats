# Copyright is waived. No warranty is provided. Unrestricted use and modification is permitted.

import io
from streams import FileStream


class OGG:
    def __init__(self):
        self.file_path = None
        self.stream = None
        self.sample_rate = 0
        self.num_channels = 0
        self.comments = []
        self.source_checksum = 0

    def load(self, file_path):
        self.file_path = file_path
        self.stream = FileStream(self.file_path, 'rb')
        self.parse_page_header()
        self.parse_identification_header()
        self.parse_page_header()
        self.parse_comment_header()

        # When encoding OGG we store the checksum of the source audio file as a comment
        for comment in self.comments:
            if comment.find('source=') == 0:
                checksum_string = comment[7:]
                self.source_checksum = int(checksum_string)

        self.stream.close()

    def get_sample_rate(self):
        return self.sample_rate

    def get_num_channels(self):
        return self.num_channels

    def get_source_checksum(self):
        return self.source_checksum

    def parse_page_header(self):
        capture_pattern = self.stream.read_u32()
        version = self.stream.read_u8()
        header_type = self.stream.read_u8()
        granule_position = self.stream.read_u64()
        bitstream_serial_number = self.stream.read_u32()
        page_sequence_number = self.stream.read_u32()
        crc_checksum = self.stream.read_u32()
        page_segments = self.stream.read_u8()
        self.stream.set_position(page_segments, io.SEEK_CUR)

    def parse_identification_header(self):
        vorbis_packet_type = self.stream.read_u8()
        vorbis_identifier = self.stream.read_u32()
        vorbis_identifier_high = self.stream.read_u16()
        vorbis_version = self.stream.read_u32()
        self.num_channels = self.stream.read_u8()
        self.sample_rate = self.stream.read_u32()
        vorbis_bitrate_maximum = self.stream.read_u32()
        vorbis_bitrate_nominal = self.stream.read_u32()
        vorbis_bitrate_minimum = self.stream.read_u32()
        vorbis_blocksize = self.stream.read_u8()
        vorbis_framing_flag = (self.stream.read_u8() & 0x01) != 0

    def parse_comment_header(self):
        vorbis_packet_type = self.stream.read_u8()
        vorbis_identifier = self.stream.read_u32()
        vorbis_identifier_high = self.stream.read_u16()
        vorbis_vector_length = self.stream.read_u32()
        vorbis_vector_name = self.stream.read_string(vorbis_vector_length)
        comment_list_length = self.stream.read_u32()
        for i in range(comment_list_length):
            comment_length = self.stream.read_u32()
            comment = self.stream.read_string(comment_length)
            self.comments.append(comment)
        vorbis_framing_bit = self.stream.read_u8() & 0x01
