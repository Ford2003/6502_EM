from cpu import CPU6502
from memory import RAM64K
from data_types import Word, Byte

if __name__ == '__main__':
    memory = RAM64K()
    # Start program just after the stack and zero page addresses
    memory[Word(0xFFFC)] = Byte(0x00)
    memory[Word(0xFFFD)] = Byte(0x02)

    memory[Word(0x0200)] = Byte(0x08)
    memory[Word(0x0201)] = Byte(0x28)

    cpu = CPU6502(memory)

    cpu.run()
