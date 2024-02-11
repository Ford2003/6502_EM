from exceptions import *
from addressing_modes import addressing_modes_6502
from tools import *


class CPU6502:
    def __init__(self, memory):
        # Registers
        self.a = 0xA3
        self.x = 0xD
        self.y = 4
        # Program Counter
        self.pc = 0
        # Stack Pointer
        self.sp = 0
        # Status Flags
        self.flags = {
            'C': False,  # Carry flag
            'Z': False,  # Zero flag
            'I': False,  # Disable interrupts
            'D': False,  # Decimal mode
            'B': False,  # Break command
            'U': False,  # Unused
            'V': False,  # Overflow flag
            'N': False,  # Negative flag
        }
        self.memory = memory

        self.addressing_mode = addressing_modes_6502

        self.OPCODES = {
            # BRK
            0x00: (self.brk, self.addressing_mode['implied']),
            # LDA
            0xA9: (self.lda, self.addressing_mode['immediate']),
            0xA5: (self.lda, self.addressing_mode['zero_page']),
            0xB5: (self.lda, self.addressing_mode['zero_page_x']),
            0xAD: (self.lda, self.addressing_mode['absolute']),
            0xBD: (self.lda, self.addressing_mode['absolute_x']),
            0xB9: (self.lda, self.addressing_mode['absolute_y']),
            0xA1: (self.lda, self.addressing_mode['indirect_x']),
            0xB1: (self.lda, self.addressing_mode['indirect_y']),
            # LDX
            0xA2: (self.ldx, self.addressing_mode['immediate']),
            0xA6: (self.ldx, self.addressing_mode['zero_page']),
            0xB6: (self.ldx, self.addressing_mode['zero_page_y']),
            0xAE: (self.ldx, self.addressing_mode['absolute']),
            0xBE: (self.ldx, self.addressing_mode['absolute_y']),
            # LDY
            0xA0: (self.ldy, self.addressing_mode['immediate']),
            0xA4: (self.ldy, self.addressing_mode['zero_page']),
            0xB4: (self.ldy, self.addressing_mode['zero_page_x']),
            0xAC: (self.ldy, self.addressing_mode['absolute']),
            0xBC: (self.ldy, self.addressing_mode['absolute_x']),
            # LSR
            0x4A: (self.lsr, self.addressing_mode['accumulator']),
            0x46: (self.lsr, self.addressing_mode['zero_page']),
            0x56: (self.lsr, self.addressing_mode['zero_page_x']),
            0x4E: (self.lsr, self.addressing_mode['absolute']),
            0x5E: (self.lsr, self.addressing_mode['absolute_x']),
            # NOP
            0xEA: (self.nop, self.addressing_mode['implied']),
        }

        self.reset()

    def reset(self):
        lsb_addr = self.get_byteADDR(0xFFFC)
        msb_addr = self.get_byteADDR(0xFFFD)
        self.pc = make_addr(lsb_addr, msb_addr)

    def run(self):
        while True:
            self.execute()

    def execute(self):
        # Fetch the opcode
        opcode = self.get_bytePC()
        func, addressing_mode = self.OPCODES[opcode]
        func(addressing_mode)

    def get_bytePC(self) -> int:
        data = self.memory[self.pc]
        if data < 0 or data > 0xFF:
            raise ByteError(f'Value {data} out of range not a byte')
        self.pc += 1
        return data

    def get_byteADDR(self, address: int) -> int:
        data = self.memory[address]
        if data < 0 or data > 0xFF:
            raise ByteError(f'Value {data} out of range not a byte')
        return data

    def store_byteADDR(self, address: int, value: int):
        if value < 0 or value > 0xFF:
            raise ByteError(f'Value {value} out of range not a byte')
        self.memory[address] = value

    def lda(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['immediate']:
            value = self.get_bytePC()
            self.a = value
        elif addressing_mode == self.addressing_mode['zero_page']:
            # msb of address is 0x00 for zero page
            address = self.get_bytePC()
            value = self.get_byteADDR(address)
            self.a = value
        elif addressing_mode == self.addressing_mode['zero_page_x']:
            # Address is zero page + x and wraps around if it goes over 0xFF
            address = (self.get_bytePC() + self.x) % (0xFF + 1)
            value = self.get_byteADDR(address)
            self.a = value
        elif addressing_mode == self.addressing_mode['absolute']:
            # Get the address from the next two bytes
            lsb = self.get_bytePC()
            msb = self.get_bytePC()
            address = make_addr(lsb, msb)
            value = self.get_byteADDR(address)
            self.a = value
        elif (addressing_mode == self.addressing_mode['absolute_x']
              or addressing_mode == self.addressing_mode['absolute_y']):
            # Get the address from the next two bytes and add x to it
            lsb = self.get_bytePC()
            msb = self.get_bytePC()
            if addressing_mode == self.addressing_mode['absolute_x']:
                address = (make_addr(lsb, msb) + self.x) % (0xFFFF + 1)
            else:
                address = (make_addr(lsb, msb) + self.y) % (0xFFFF + 1)
            value = self.get_byteADDR(address)
            self.a = value
        elif addressing_mode == self.addressing_mode['indirect_x']:
            # Get the zero page address from the next byte and add x to it
            address = (self.get_bytePC() + self.x) % (0xFF + 1)
            # Get the lsb and msb from the zero page address and the next zero page address
            lsb = self.get_byteADDR(address)
            msb = self.get_byteADDR((address + 1) % (0xFF + 1))
            # Get the value from the address formed by the lsb and msb
            value = self.get_byteADDR(make_addr(lsb, msb))
            self.a = value
        elif addressing_mode == self.addressing_mode['indirect_y']:
            # get the zero page address from the next byte
            address = self.get_bytePC()
            # get the lsb and msb from the zero page address and the next zero page address
            lsb = self.get_byteADDR(address)
            msb = self.get_byteADDR((address + 1) % (0xFF + 1))
            # get the value from the address formed by the lsb and msb and add y to it
            value = self.get_byteADDR(make_addr(lsb, msb) + self.y)
            self.a = value
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')

        # Update flags
        self.flags['Z'] = self.a == 0
        self.flags['N'] = self.a & 0b10000000 > 0

    def ldx(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['immediate']:
            value = self.get_bytePC()
            self.x = value
        elif addressing_mode == self.addressing_mode['zero_page']:
            # msb of address is 0x00 for zero page
            address = self.get_bytePC()
            value = self.get_byteADDR(address)
            self.x = value
        elif addressing_mode == self.addressing_mode['zero_page_y']:
            # Address is zero page + y and wraps around if it goes over 0xFF
            address = (self.get_bytePC() + self.y) % (0xFF + 1)
            value = self.get_byteADDR(address)
            self.x = value
        elif addressing_mode == self.addressing_mode['absolute']:
            # next 2 bytes make the address
            lsb = self.get_bytePC()
            msb = self.get_bytePC()
            addr = make_addr(lsb, msb)
            value = self.get_byteADDR(addr)
            self.x = value
        elif addressing_mode == self.addressing_mode['absolute_y']:
            # next 2 bytes make the address
            lsb = self.get_bytePC()
            msb = self.get_bytePC()
            addr = (make_addr(lsb, msb) + self.y) % (0xFFFF + 1)
            value = self.get_byteADDR(addr)
            self.x = value
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')
        # Update flags
        self.flags['Z'] = self.x == 0
        self.flags['N'] = self.x & 0b10000000 > 0

    def ldy(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['immediate']:
            value = self.get_bytePC()
            self.y = value
        elif addressing_mode == self.addressing_mode['zero_page']:
            # msb of address is 0x00 for zero page
            address = self.get_bytePC()
            value = self.get_byteADDR(address)
            self.y = value
        elif addressing_mode == self.addressing_mode['zero_page_x']:
            # Address is zero page + x and wraps around if it goes over 0xFF
            address = (self.get_bytePC() + self.x) % (0xFF + 1)
            value = self.get_byteADDR(address)
            self.y = value
        elif addressing_mode == self.addressing_mode['absolute']:
            # next 2 bytes make the address
            lsb = self.get_bytePC()
            msb = self.get_bytePC()
            addr = make_addr(lsb, msb)
            value = self.get_byteADDR(addr)
            self.y = value
        elif addressing_mode == self.addressing_mode['absolute_x']:
            lsb = self.get_bytePC()
            msb = self.get_bytePC()
            addr = (make_addr(lsb, msb) + self.x) % (0xFFFF + 1)
            value = self.get_byteADDR(addr)
            self.y = value
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')

        self.flags['Z'] = self.y == 0
        self.flags['N'] = self.y & 0b10000000 > 0

    def lsr(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['accumulator']:
            # shift value in accumulator right.
            self.flags['C'] = self.a & 1 == 1
            self.a >>= 1
            value = self.a
        elif addressing_mode == self.addressing_mode['zero_page']:
            # load zero page address, shift right, store back.
            address = self.get_bytePC()
            value = self.get_byteADDR(address)
            self.flags['C'] = value & 1 == 1
            value >>= 1
            self.store_byteADDR(address, value)
        elif addressing_mode == self.addressing_mode['zero_page_x']:
            # load zero page address + x, shift right, store back.
            address = (self.get_bytePC() + self.x) % (0xFF + 1)
            value = self.get_byteADDR(address)
            self.flags['C'] = value & 1 == 1
            value >>= 1
            self.store_byteADDR(address, value)
        elif addressing_mode == self.addressing_mode['absolute']:
            # load absolute address, shift right, store back.
            lsb = self.get_bytePC()
            msb = self.get_bytePC()
            address = make_addr(lsb, msb)
            value = self.get_byteADDR(address)
            self.flags['C'] = value & 1 == 1
            value >>= 1
            self.store_byteADDR(address, value)
        elif addressing_mode == self.addressing_mode['absolute_x']:
            # load absolute address + x, shift right, store back.
            lsb = self.get_bytePC()
            msb = self.get_bytePC()
            address = (make_addr(lsb, msb) + self.x) % (0xFFFF + 1)
            value = self.get_byteADDR(address)
            self.flags['C'] = value & 1 == 1
            value >>= 1
            self.store_byteADDR(address, value)
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')

        # Update flags.
        self.flags['Z'] = value == 0
        self.flags['N'] = value & 0x80 > 0

    def nop(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['implied']:
            pass
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')

    def brk(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['implied']:
            self.flags['B'] = True
            raise InterruptError('BRK instruction encountered')
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')


# indirect x: add x and byte with wrap around. get lsb from memory from this zero page address.
# get msb from next zero page address.
