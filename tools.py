from data_types import Word, Byte


def make_addr(lsb: Byte, msb: Byte) -> Word:
    return Word((msb << 8) | lsb)
