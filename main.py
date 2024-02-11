from cpu import CPU6502

if __name__ == '__main__':
    memory = [0] * (0xFFFF + 1)
    # Start program just after the stack and zero page addresses
    memory[0xFFFC] = 0x00
    memory[0xFFFD] = 0x02

    # lsr a
    memory[0x0200] = 0xEA
    memory[0x0201] = 0xA9
    memory[0x0202] = 0x05





    cpu = CPU6502(memory)

    cpu.run()
