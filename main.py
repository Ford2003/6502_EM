from cpu import CPU6502

if __name__ == '__main__':
    memory = [0] * (0xFFFF + 1)
    # Start program just after the stack and zero page addresses
    memory[0xFFFC] = 0x00
    memory[0xFFFD] = 0x02

    # load 5A into the accumulator
    memory[0x0200] = 0xA9
    memory[0x0201] = 0x5A

    memory[0x0202] = 0xEA





    cpu = CPU6502(memory)

    cpu.run()
