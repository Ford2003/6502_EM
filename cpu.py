from exceptions import *
from addressing_modes import addressing_modes_6502
from tools import *
from collections import OrderedDict


class CPU6502:
    def __init__(self, memory):
        # Registers
        self.a = 0xA3
        self.x = 0xD
        self.y = 4
        # Program Counter
        self.pc = 0
        # Stack Pointer - Stack memory range is 0x0100 to 0x01FF
        self.sp = 0
        # Status Flags
        self.flags = OrderedDict({
            'C': False,  # Carry flag
            'Z': False,  # Zero flag
            'I': True,  # Disable interrupts
            'D': True,  # Decimal mode
            'B': False,  # Break command
            'U': True,  # Unused
            'V': False,  # Overflow flag
            'N': True,  # Negative flag
        })
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
            # ORA
            0x09: (self.ora, self.addressing_mode['immediate']),
            0x05: (self.ora, self.addressing_mode['zero_page']),
            0x15: (self.ora, self.addressing_mode['zero_page_x']),
            0x0D: (self.ora, self.addressing_mode['absolute']),
            0x1D: (self.ora, self.addressing_mode['absolute_x']),
            0x19: (self.ora, self.addressing_mode['absolute_y']),
            0x01: (self.ora, self.addressing_mode['indirect_x']),
            0x11: (self.ora, self.addressing_mode['indirect_y']),
            # PHA
            0x48: (self.pha, self.addressing_mode['implied']),
            # PLA
            0x68: (self.pla, self.addressing_mode['implied']),
            # PHP
            0x08: (self.php, self.addressing_mode['implied']),
            # PLP
            0x28: (self.plp, self.addressing_mode['implied']),
        }

        self.reset()

    def reset(self):
        lsb_addr = self.get_byteADDR(0xFFFC)
        msb_addr = self.get_byteADDR(0xFFFD)
        self.pc = make_addr(lsb_addr, msb_addr)
        self.sp = 0xFF

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

    def get_absolute_address(self) -> int:
        lsb = self.get_bytePC()
        msb = self.get_bytePC()
        return make_addr(lsb, msb)

    def get_indirect_x_address(self) -> int:
        address = (self.get_bytePC() + self.x) % (0xFF + 1)
        lsb = self.get_byteADDR(address)
        msb = self.get_byteADDR((address + 1) % (0xFF + 1))
        return make_addr(lsb, msb)

    def get_indirect_y_address(self) -> int:
        address = self.get_bytePC()
        lsb = self.get_byteADDR(address)
        msb = self.get_byteADDR((address + 1) % (0xFF + 1))
        return (make_addr(lsb, msb) + self.y) % (0xFFFF + 1)

    def get_status_register(self):
        status = 0
        for value in reversed(self.flags.values()):
            status |= value
            status <<= 1
        status >>= 1
        return status

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
            address = self.get_absolute_address()
            value = self.get_byteADDR(address)
            self.a = value
        elif (addressing_mode == self.addressing_mode['absolute_x']
              or addressing_mode == self.addressing_mode['absolute_y']):
            # Get the address from the next two bytes and add x to it
            address = self.get_absolute_address()
            if addressing_mode == self.addressing_mode['absolute_x']:
                address = (address + self.x) % (0xFFFF + 1)
            else:
                address = (address + self.y) % (0xFFFF + 1)
            value = self.get_byteADDR(address)
            self.a = value
        elif addressing_mode == self.addressing_mode['indirect_x']:
            address = self.get_indirect_x_address()
            value = self.get_byteADDR(address)
            self.a = value
        elif addressing_mode == self.addressing_mode['indirect_y']:
            address = self.get_indirect_y_address()
            value = self.get_byteADDR(address)
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
            address = self.get_absolute_address()
            value = self.get_byteADDR(address)
            self.x = value
        elif addressing_mode == self.addressing_mode['absolute_y']:
            # next 2 bytes make the address
            address = (self.get_absolute_address() + self.y) % (0xFFFF + 1)
            value = self.get_byteADDR(address)
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
            address = self.get_absolute_address()
            value = self.get_byteADDR(address)
            self.y = value
        elif addressing_mode == self.addressing_mode['absolute_x']:
            address = (self.get_absolute_address() + self.x) % (0xFFFF + 1)
            value = self.get_byteADDR(address)
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
            address = self.get_absolute_address()
            value = self.get_byteADDR(address)
            self.flags['C'] = value & 1 == 1
            value >>= 1
            self.store_byteADDR(address, value)
        elif addressing_mode == self.addressing_mode['absolute_x']:
            # load absolute address + x, shift right, store back.
            address = (self.get_absolute_address() + self.x) % (0xFFFF + 1)
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

    def ora(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['immediate']:
            value = self.get_bytePC()
            self.a |= value
        elif addressing_mode == self.addressing_mode['zero_page']:
            address = self.get_bytePC()
            value = self.get_byteADDR(address)
            self.a |= value
        elif addressing_mode == self.addressing_mode['zero_page_x']:
            address = (self.get_bytePC() + self.x) % (0xFF + 1)
            value = self.get_byteADDR(address)
            self.a |= value
        elif addressing_mode == self.addressing_mode['absolute']:
            address = self.get_absolute_address()
            value = self.get_byteADDR(address)
            self.a |= value
        elif addressing_mode == self.addressing_mode['absolute_x']:
            address = (self.get_absolute_address() + self.x) % (0xFFFF + 1)
            value = self.get_byteADDR(address)
            self.a |= value
        elif addressing_mode == self.addressing_mode['absolute_y']:
            address = (self.get_absolute_address() + self.y) % (0xFFFF + 1)
            value = self.get_byteADDR(address)
            self.a |= value
        elif addressing_mode == self.addressing_mode['indirect_x']:
            address = self.get_indirect_x_address()
            value = self.get_byteADDR(address)
            self.a |= value
        elif addressing_mode == self.addressing_mode['indirect_y']:
            address = self.get_indirect_y_address()
            value = self.get_byteADDR(address)
            self.a |= value
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')

        # Update flags
        self.flags['Z'] = self.a == 0
        self.flags['N'] = self.a & 0x80 > 0

    def pha(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['implied']:
            self.store_byteADDR(0x0100 + self.sp, self.a)
            if self.sp == 0:
                self.sp = 0xFF
            else:
                self.sp -= 1
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')

    def pla(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['implied']:
            if self.sp == 0xFF:
                # Loop stack around to 0x0100
                self.sp = 0
            else:
                self.sp += 1
            self.a = self.get_byteADDR(0x0100 + self.sp)
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')

        # Update flags
        self.flags['Z'] = self.a == 0
        self.flags['N'] = self.a & 0x80 > 0

    def php(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['implied']:
            # Push status register to stack
            self.store_byteADDR(0x0100 + self.sp, self.get_status_register())
            if self.sp == 0:
                self.sp = 0xFF
            else:
                self.sp -= 1
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')
        print()

    def plp(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['implied']:
            if self.sp == 0xFF:
                self.sp = 0
            else:
                self.sp += 1
            status = self.get_byteADDR(0x0100 + self.sp)
            for flag in self.flags.keys():
                self.flags[flag] = status & 1
                status >>= 1
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')
        print()

    def brk(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['implied']:
            self.flags['B'] = True
            raise InterruptError('BRK instruction encountered')
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')


# indirect x: add x and byte with wrap around. get lsb from memory from this zero page address.
# get msb from next zero page address.
