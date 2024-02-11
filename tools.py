def make_addr(lsb: int, msb: int) -> int:
    return (msb << 8) | lsb
