# 6502_EM
A 6502 CPU emulator built in Python.

<ins>Technologies Used</ins>
- Python
- OOP
- Data Structures

Currently has about ~half the instructions made for 6502 CPU [here's](http://www.6502.org/users/obelisk/6502/) a reference to its documentation.

This program has a CPU6502 class which contains the functionality and runs in an infinite loop, it also has a base abstract Memory class and come standard memory module classes such as RAM64K which contains 64KB of storage. You can input the bytes data into the Memory module and then create a CPU6502 object and pass it a reference to the memory object and run the CPU.

I have also created a base data type class for handling binary operations and making sure a values stay within the allowed ranges. There are 3 children classes of this base class: Bit, Byte and Word.

<ins>About the CPU</ins>
- It's little endian
- Has different addressing modes with different addressing modes for each instruction (immediate, implied, absolute, etc)
- Has 3 registers: accumulator, x, y
- Has a program counter for getting instructions and data sequentially from memory
- Has a byte for processing status flags (zero bit, carry bit, negative bit, etc)
- Has a stack pointer, stack ranges from 0x0100 - 0x01FF.

Example usage of loading the value 0xD3 into the 'a' register:

```python
from memory import RAM64K
from cpu import CPU6502
from data_types import Word, Byte

if __name__ == "__main__":
  # Instantiate a memory object with 64KB of memory.
  memory = RAM64K()

  # This tells the CPU where the program counter should start in this example 0x0200 as this cpu is little endian, 0x0200 is just after the stack.
  memory[Word(0xFFFC)] = Byte(0x00)
  memory[Word(0xFFFD)] = Byte(0x02)

  # LDA $D3
  memory[Word(0x0200)] = Byte(0xA9)
  memory[Word(0x0201)] = Byte(0xD3)
  cpu = CPU6502(memory)

  cpu.run()
```
