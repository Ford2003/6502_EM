from data_types import Word, Byte


def make_addr(lsb: Byte, msb: Byte) -> Word:
    return Word((msb.value << 8) | lsb.value)
