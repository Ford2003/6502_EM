from exceptions import *
from addressing_modes import addressing_modes_6502
from tools import *


class CPU6502:
    def __init__(self, memory):
        # Registers
        self.a = 0
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
            0x00: (self.brk, self.addressing_mode['implied']),
            0xA9: (self.lda, self.addressing_mode['immediate']),
            0xA5: (self.lda, self.addressing_mode['zero_page']),
            0xB5: (self.lda, self.addressing_mode['zero_page_x']),
            0xAD: (self.lda, self.addressing_mode['absolute']),
            0xBD: (self.lda, self.addressing_mode['absolute_x']),
            0xB9: (self.lda, self.addressing_mode['absolute_y']),
            0xA1: (self.lda, self.addressing_mode['indirect_x']),
            0xB1: (self.lda, self.addressing_mode['indirect_y']),
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
        if data < 0 or data > 255:
            raise ByteError(f'Value {data} out of range not a byte')
        self.pc += 1
        return data

    def get_byteADDR(self, address: int) -> int:
        data = self.memory[address]
        if data < 0 or data > 255:
            raise ByteError(f'Value {data} out of range not a byte')
        return data

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
        elif addressing_mode == self.addressing_mode['absolute_x'] or addressing_mode == self.addressing_mode['absolute_y']:
            # Get the address from the next two bytes and add x to it
            lsb = self.get_bytePC()
            msb = self.get_bytePC()
            # TODO: Check how 6502 handles overflow in absolute x addressing mode
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

    def brk(self, addressing_mode: int):
        self.flags['B'] = True
        raise InterruptError('BRK instruction encountered')


# indirect x: add x and byte with wrap around. get lsb from memory from this zero page address.
# get msb from next zero page address.
