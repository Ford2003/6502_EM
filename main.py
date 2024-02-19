from cpu import CPU6502

if __name__ == '__main__':
    memory = [0] * (0xFFFF + 1)
    # Start program just after the stack and zero page addresses
    memory[0xFFFC] = 0x00
    memory[0xFFFD] = 0x02

    memory[0x0200] = 0x08
    memory[0x0201] = 0x28


    cpu = CPU6502(memory)

    cpu.run()
