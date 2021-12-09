# Copyright is waived. No warranty is provided. Unrestricted use and modification is permitted.

import io
import sys
from streams import FileStream

version_table = ['2.5', 'reserved', '2', '1']

bit_rate_table = {
    3: {    # MPEG V1
        3: ['free', 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448, 'bad'],    # Layer I
        2: ['free', 32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384, 'bad'],       # Layer II
        1: ['free', 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 'bad']         # Layer III
    },
    2: {    # MPEG V2
        3: ['free', 32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256, 'bad'],  # Layer I
        2: ['free', 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 'bad'],       # Layer II
        1: ['free', 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 'bad'],       # Layer III
    }
}

sample_rate_table = {
    2: [22050, 24000, 16000, 'reserved'],       # MPEG V2
    3: [44100, 48000, 32000, 'reserved']        # MPEG V1
}

channel_mode_table = ['Stereo', 'Joint Stereo', 'Dual Channel', 'Single Channel']


class MP3:

    def __init__(self):
        self.file_path = None
        self.mpeg_version = None
        self.layer_index = None
        self.protection = None
        self.bitrate_index = None
        self.sample_rate_index = None
        self.padding_flag = None
        self.private_flag = None
        self.channel_mode = None

        self.version = None
        self.layer = None
        self.bit_rate = 0
        self.sample_rate = 0
        self.channel_mode = 0
        self.channel_mode_name = None
        self.comment = None

    def load(self, file_path):
        self.file_path = file_path
        stream = FileStream(self.file_path, 'rb', FileStream.BIG_ENDIAN)

        # Parse the ID3 tag if present
        id3_pattern = stream.read_string(3)
        if id3_pattern == 'ID3':
            id3_version = stream.read_u16()
            id3_flags = stream.read_u8()

            # Get size of ID3 tag;  excludes header information, so the real size is this size plus 10 bytes
            id3_size = (stream.read_u8() << 21) + (stream.read_u8() << 14) + (stream.read_u8() << 7) + stream.read_u8()

            # Check for extended header
            if id3_flags & 0x40 == 0x40:
                sys.exit('Extended header not currently handled')

            # Parse frames within the ID3 tag
            while stream.get_position() < (id3_size + 10):
                frame_id = stream.read_string(4)
                frame_size = stream.read_u32()
                frame_flags = stream.read_u16()

                # Comment tag
                if frame_id == 'COMM':
                    text_encoding = stream.read_u8()
                    language = stream.read_string(3)
                    remainder = frame_size - 4

                    # Read description
                    if text_encoding == 0:                      # ISO-8859-1 encoding
                        description = stream.read_nt_string()
                        remainder -= (len(description) + 1)
                    elif text_encoding == 1:                    # UCS-2 encoded Unicode with BOM
                        description = stream.read_nt_utf16_string()
                        remainder -= (len(description) + 1) * 2
                    elif text_encoding == 2:                    # UTF-16BE encoded Unicode without BOM
                        sys.exit('ERROR: Unsupported text encoding in COMM frame')
                    elif text_encoding == 3:                    # UTF-8 encoded Unicode
                        sys.exit('ERROR: Unsupported text encoding in COMM frame')
                    else:
                        sys.exit('ERROR: Invalid text encoding in COMM frame')

                    # Read comment
                    if text_encoding == 0:                      # ISO-8859-1 encoding
                        self.comment = stream.read_string(remainder)
                    elif text_encoding == 1:                    # UCS-2 encoded Unicode with BOM
                        self.comment = stream.read_utf16_string(remainder/2)
                    elif text_encoding == 2:                    # UTF-16BE encoded Unicode without BOM
                        sys.exit('ERROR: Unsupported text encoding in COMM frame')
                    elif text_encoding == 3:                    # UTF-8 encoded Unicode
                        sys.exit('ERROR: Unsupported text encoding in COMM frame')
                    else:
                        sys.exit('ERROR: Invalid text encoding in COMM frame')

                else:
                    stream.set_position(frame_size, io.SEEK_CUR)
        else:
            # Not an ID3 tag so reset stream pointer to start
            stream.set_position(0)

        # Now parse the MP3 data
        frame_header = stream.read_u32()
        if frame_header & 0xffc00000 == 0xffc00000:
            self.mpeg_version = (frame_header >> 19) & 0x03
            self.layer_index = (frame_header >> 17) & 0x03
            self.protection = (frame_header >> 16) & 0x01
            self.bitrate_index = (frame_header >> 12) & 0x0f
            self.sample_rate_index = (frame_header >> 10) & 0x03
            self.padding_flag = (frame_header >> 9) & 0x01
            self.private_flag = (frame_header >> 8) & 0x01
            self.channel_mode = (frame_header >> 6) & 0x03

            self.version = version_table[self.mpeg_version]
            self.layer = 4 - self.layer_index
            self.bit_rate = bit_rate_table[self.mpeg_version][self.layer_index][self.bitrate_index]
            self.sample_rate = sample_rate_table[self.mpeg_version][self.sample_rate_index]
            self.channel_mode_name = channel_mode_table[self.channel_mode]
        else:
            print ('ERROR: Frame synchronization not found')

        stream.close()

    def get_version(self):
        return self.version

    def get_layer(self):
        return self.layer

    def get_bit_rate(self):
        return self.bit_rate

    def get_sample_rate(self):
        return self.sample_rate

    def get_channel_mode(self):
        return self.channel_mode_name

    def get_comment(self):
        return self.comment
