from memory import RAM64K
from cpu import CPU6502
from clock import Clock1Hz
from data_types import Word, Byte
import threading


if __name__ == "__main__":
    # Instantiate a memory object with 64KB of memory.
    memory = RAM64K()

    # This tells the CPU where the program counter should start in this example 0x0200 as this cpu is little endian,
    # 0x0200 is just after the stack.
    memory[Word(0xFFFC)] = Byte(0x00)
    memory[Word(0xFFFD)] = Byte(0x02)

    # LDA $D3
    memory[Word(0x0200)] = Byte(0xB5)
    memory[Word(0x0201)] = Byte(0xF2)
    memory[Word(0x0034)] = Byte(0xC3)

    clock = Clock1Hz()
    cpu = CPU6502(memory, clock)

    cpu_thread = threading.Thread(target=cpu.run)

    clock.start()
    cpu_thread.start()
