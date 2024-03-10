from exceptions import *
from addressing_modes import addressing_modes_6502
from tools import *
from collections import OrderedDict
from data_types import Word, Byte, Bit, DType
from memory import Memory
from clock import Clock
from threading import Thread


class CPU6502:
    def __init__(self, memory: Memory, clock: Clock):
        # Registers
        self.a = Byte(0)
        self.x = Byte(0x42)
        self.y = Byte(0)
        # Program Counter
        self.pc = Word(0x0200)
        # Stack Pointer - Stack memory range is 0x0100 to 0x01FF
        self.sp = Byte(0xFF)
        # Status Flags
        self.flags = OrderedDict({
            'C': Bit(False),  # Carry flag
            'Z': Bit(False),  # Zero flag
            'I': Bit(False),  # Disable interrupts
            'D': Bit(False),  # Decimal mode
            'B': Bit(False),  # Break command
            'U': Bit(False),  # Unused
            'V': Bit(False),  # Overflow flag
            'N': Bit(False),  # Negative flag
        })
        self.memory = memory
        self.clock = clock

        self._cpu_thread = Thread(target=self.run)

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

    def reset(self):
        lsb_addr = self.clock.schedule(self.get_byteADDR, Word(0xFFFC))
        self.wait_for_pulse()
        msb_addr = self.clock.schedule(self.get_byteADDR, Word(0xFFFD))
        self.wait_for_pulse()
        self.pc = make_addr(lsb_addr, msb_addr)
        self.sp.value = 0xFF

    def start(self):
        self._cpu_thread.start()

    def run(self):
        # self.clock.schedule(self.reset)
        while True:
            self.clock.schedule(self.execute)

    def execute(self):
        # Fetch the opcode
        opcode = self.clock.schedule(self.get_bytePC)
        func, addressing_mode = self.OPCODES[opcode.value]
        print(f'running {func.__name__}')
        self.clock.schedule(func, addressing_mode)

    def wait_for_pulse(self):
        self.clock.wait_for_pulse()

    def get_bytePC(self) -> Byte:
        # Getting a byte from memory will always take a full cycle
        self.wait_for_pulse()
        data = self.memory[self.pc]
        self.pc += 1
        return data

    def get_byteADDR(self, address: Word | Byte) -> Byte:
        self.wait_for_pulse()
        return self.memory[address]

    def store_byteADDR(self, address: Word | Byte, value: Byte):
        self.wait_for_pulse()
        self.memory[address] = value

    def get_absolute_address(self) -> Word:
        # Takes 2 cycles
        lsb = self.clock.schedule(self.get_bytePC)
        msb = self.clock.schedule(self.get_bytePC)
        return make_addr(lsb, msb)

    def get_indirect_x_address(self) -> Word:
        address = self.clock.schedule(self.get_bytePC)
        address = self.clock.schedule(self.add_x, address, zero_page=True)
        lsb = self.clock.schedule(self.get_byteADDR, address)
        msb = self.clock.schedule(self.get_byteADDR, address + 1)
        return make_addr(lsb, msb)

    def get_indirect_y_address(self) -> Word:
        address = self.clock.schedule(self.get_bytePC)
        address = Word(address.value)
        lsb = self.clock.schedule(self.get_byteADDR, address)
        msb = self.clock.schedule(self.get_byteADDR, address + 1)
        address = make_addr(lsb, msb)
        address = self.clock.schedule(self.add_y, address, do_cycle=False)
        return address

    def get_status_register(self) -> Byte:
        status = 0
        for bit in reversed(self.flags.values()):
            status |= bit.value
            status <<= 1
        status >>= 1
        return Byte(status)

    def add_x(self, value: DType, zero_page: bool = False, do_cycle: bool = True) -> DType:
        # takes 1 cycle to add x register
        if not isinstance(value, DType):
            raise TypeError(f'Expected DType, got {value.__class__.__name__}')
        if do_cycle:
            self.wait_for_pulse()
        if not zero_page and (self.x.value + value.value) % (Byte.max_value + 1) < self.x.value:
            # + 1 cycle for page crossing
            self.wait_for_pulse()

        return value + self.x

    def add_y(self, value: DType, zero_page: bool = False, do_cycle: bool = True) -> DType:
        # takes 1 cycle to add y register
        if not isinstance(value, DType):
            raise TypeError(f'Expected DType, got {value.__class__.__name__}')
        if do_cycle:
            self.wait_for_pulse()
        if not zero_page and (self.y.value + value.value) % (Byte.max_value + 1) < self.y.value:
            # + 1 cycle for page crossing
            self.wait_for_pulse()

        return value + self.y

    def lda(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['immediate']:
            # 2 Cycles
            value = self.clock.schedule(self.get_bytePC)
            self.a = value
        elif addressing_mode == self.addressing_mode['zero_page']:
            # 3 Cycles
            # msb of address is 0x00 for zero page
            address = self.clock.schedule(self.get_bytePC)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.a = value
        elif addressing_mode == self.addressing_mode['zero_page_x']:
            # 4 Cycles
            # Address is zero page + x and wraps around if it goes over 0xFF
            address = self.clock.schedule(self.get_bytePC)
            # Add x to address, takes 1 cycle.
            address = self.clock.schedule(self.add_x, address, zero_page=True)
            # Fetch the value at the address, takes 1 cycle.
            value = self.clock.schedule(self.get_byteADDR, address)
            self.a = value
        elif addressing_mode == self.addressing_mode['absolute']:
            # 4 Cycles
            # Get the address from the next two bytes
            address = self.clock.schedule(self.get_absolute_address)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.a = value
        elif (addressing_mode == self.addressing_mode['absolute_x']
              or addressing_mode == self.addressing_mode['absolute_y']):
            # 4 Cycles + 1 if page crossed
            # Get the address from the next two bytes and add x to it
            address = self.clock.schedule(self.get_absolute_address)  # 2 cycles
            if addressing_mode == self.addressing_mode['absolute_x']:
                address = self.clock.schedule(self.add_x, address, do_cycle=False)
            else:
                address = self.clock.schedule(self.add_y, address, do_cycle=False)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.a = value
        elif addressing_mode == self.addressing_mode['indirect_x']:
            # 6 Cycles
            address = self.clock.schedule(self.get_indirect_x_address)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.a = value
        elif addressing_mode == self.addressing_mode['indirect_y']:
            # 5 Cycles + 1 if page crossed
            address = self.clock.schedule(self.get_indirect_y_address)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.a = value
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')

        # Update flags
        self.flags['Z'] = self.a == 0
        self.flags['N'] = self.a & 0b10000000 > 0

    def ldx(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['immediate']:
            value = self.clock.schedule(self.get_bytePC)
            self.x = value
        elif addressing_mode == self.addressing_mode['zero_page']:
            # msb of address is 0x00 for zero page
            address = self.clock.schedule(self.get_bytePC)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.x = value
        elif addressing_mode == self.addressing_mode['zero_page_y']:
            # Address is zero page + y and wraps around if it goes over 0xFF
            address = self.clock.schedule(self.get_bytePC)
            address = self.clock.schedule(self.add_y, address, zero_page=True, do_cycle=True)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.x = value
        elif addressing_mode == self.addressing_mode['absolute']:
            # next 2 bytes make the address
            address = self.clock.schedule(self.get_absolute_address)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.x = value
        elif addressing_mode == self.addressing_mode['absolute_y']:
            # next 2 bytes make the address
            address = self.clock.schedule(self.get_absolute_address)
            address = self.clock.schedule(self.add_y, address, do_cycle=False)
            value = self.get_byteADDR(address)
            self.x = value
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')
        # Update flags
        self.flags['Z'] = self.x == 0
        self.flags['N'] = self.x & 0b10000000 > 0

    def ldy(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['immediate']:
            value = self.clock.schedule(self.get_bytePC)
            self.y = value
        elif addressing_mode == self.addressing_mode['zero_page']:
            # msb of address is 0x00 for zero page
            address = self.clock.schedule(self.get_bytePC)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.y = value
        elif addressing_mode == self.addressing_mode['zero_page_x']:
            # Address is zero page + x and wraps around if it goes over 0xFF
            address = self.clock.schedule(self.get_bytePC)
            address = self.clock.schedule(self.add_x, address, zero_page=True, do_cycle=True)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.y = value
        elif addressing_mode == self.addressing_mode['absolute']:
            # next 2 bytes make the address
            address = self.clock.schedule(self.get_absolute_address)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.y = value
        elif addressing_mode == self.addressing_mode['absolute_x']:
            address = self.clock.schedule(self.get_absolute_address)
            address = self.clock.schedule(self.add_x, address, do_cycle=False)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.y = value
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')

        self.flags['Z'] = self.y == 0
        self.flags['N'] = self.y & 0b10000000 > 0

    def lsr(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['accumulator']:
            # shift value in accumulator right.
            # 2 cycles
            self.wait_for_pulse()
            self.flags['C'] = self.a & 1 == 1
            self.a >>= 1
            value = self.a
        elif addressing_mode == self.addressing_mode['zero_page']:
            # load zero page address, shift right, store back.
            # 5 cycles
            address = self.clock.schedule(self.get_bytePC)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.wait_for_pulse()
            self.flags['C'] = value & 1 == 1
            value >>= 1
            self.clock.schedule(self.store_byteADDR, address, value)
        elif addressing_mode == self.addressing_mode['zero_page_x']:
            # load zero page address + x, shift right, store back.
            # 6 Cycles
            address = self.clock.schedule(self.get_bytePC)
            address = self.clock.schedule(self.add_x, address, zero_page=True, do_cycle=True)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.wait_for_pulse()
            self.flags['C'] = value & 1 == 1
            value >>= 1
            self.clock.schedule(self.store_byteADDR, address, value)
        elif addressing_mode == self.addressing_mode['absolute']:
            # load absolute address, shift right, store back.
            # 6 Cycles
            address = self.clock.schedule(self.get_absolute_address)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.wait_for_pulse()
            self.flags['C'] = value & 1 == 1
            value >>= 1
            self.clock.schedule(self.store_byteADDR, address, value)
        elif addressing_mode == self.addressing_mode['absolute_x']:
            # load absolute address + x, shift right, store back.
            # 7 Cycles
            address = self.clock.schedule(self.get_absolute_address)
            # Use zero page mode in add as this instruction does not incur an extra cycle for page crossing.
            address = self.clock.schedule(self.add_x, address, zero_page=True, do_cycle=True)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.wait_for_pulse()
            self.flags['C'] = value & 1 == 1
            value >>= 1
            self.clock.schedule(self.store_byteADDR, address, value)
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
            value = self.clock.schedule(self.get_bytePC)
            self.a |= value
        elif addressing_mode == self.addressing_mode['zero_page']:
            address = self.clock.schedule(self.get_bytePC)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.a |= value
        elif addressing_mode == self.addressing_mode['zero_page_x']:
            address = self.clock.schedule(self.get_bytePC)
            address = self.clock.schedule(self.add_x, address, zero_page=True, do_cycle=True)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.a |= value
        elif addressing_mode == self.addressing_mode['absolute']:
            address = self.clock.schedule(self.get_absolute_address)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.a |= value
        elif addressing_mode == self.addressing_mode['absolute_x']:
            address = self.clock.schedule(self.get_absolute_address)
            address = self.clock.schedule(self.add_x, address, do_cycle=False)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.a |= value
        elif addressing_mode == self.addressing_mode['absolute_y']:
            address = self.clock.schedule(self.get_absolute_address)
            address = self.clock.schedule(self.add_y, address, do_cycle=False)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.a |= value
        elif addressing_mode == self.addressing_mode['indirect_x']:
            address = self.clock.schedule(self.get_indirect_x_address)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.a |= value
        elif addressing_mode == self.addressing_mode['indirect_y']:
            address = self.clock.schedule(self.get_indirect_y_address)
            value = self.clock.schedule(self.get_byteADDR, address)
            self.a |= value
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')

        # Update flags
        self.flags['Z'] = self.a == 0
        self.flags['N'] = self.a & 0x80 > 0

    def pha(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['implied']:
            self.clock.schedule(self.store_byteADDR, Word(0x0100) + self.sp, self.a)
            self.wait_for_pulse()
            if self.sp == 0:
                self.sp = Byte(0xFF)
            else:
                self.sp.value -= 1
                print(self.sp)
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')

    def pla(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['implied']:
            self.wait_for_pulse()
            if self.sp == 0xFF:
                # Loop stack around to 0x0100
                self.sp.value = 0
            else:
                self.sp.value += 1
            self.a = self.clock.schedule(self.get_byteADDR, Word(0x0100) + self.sp)
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')
        self.wait_for_pulse()
        # Update flags
        self.flags['Z'] = self.a == 0
        self.flags['N'] = self.a & 0x80 > 0

    def php(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['implied']:
            # Push status register to stack
            self.clock.schedule(self.store_byteADDR, Word(self.sp.value + 0x0100), self.get_status_register())
            self.wait_for_pulse()
            if self.sp == 0:
                self.sp.value = 0xFF
            else:
                self.sp.value -= 1
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')

    def plp(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['implied']:
            self.wait_for_pulse()
            if self.sp == 0xFF:
                self.sp.value = 0
            else:
                self.sp.value += 1
            status = self.clock.schedule(self.get_byteADDR, Word(0x0100) + self.sp)
            self.wait_for_pulse()
            for flag in self.flags.keys():
                self.flags[flag] = status & 1
                status >>= 1
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')

    def brk(self, addressing_mode: int):
        if addressing_mode == self.addressing_mode['implied']:
            self.flags['B'].value = 1
            self.clock.stop()
            raise InterruptError('BRK instruction encountered')
        else:
            raise AddressModeError(f'Addressing mode {addressing_mode} not implemented')


# indirect x: add x and byte with wrap around. get lsb from memory from this zero page address.
# get msb from next zero page address.
