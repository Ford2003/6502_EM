import unittest
from threading import Thread
from cpu import CPU6502
from memory import RAM64K
from data_types import Word, Byte, Bit
from exceptions import *
from clock import Clock


class MyTestCase(unittest.TestCase):
    def setUp(self):
        # Reset memory after each test
        self.memory = RAM64K()
        self.memory[Word(0xFFFC)] = Byte(0x00)
        self.memory[Word(0xFFFD)] = Byte(0x02)

        self.clock = Clock(45)

    def check_flags(self, cpu, flags):
        for flag, value in zip(['C', 'Z', 'I', 'D', 'B', 'U', 'V', 'N'], flags):
            print(flag, value, cpu.flags[flag])
            self.assertEqual(cpu.flags[flag].value, value)

    def run_cpu(self):
        self.cpu = CPU6502(self.memory, self.clock)

        self.cpu.start()
        self.clock.start()

        self.clock._clock_thread.join()
        self.cpu._cpu_thread.join()

    def test_lda(self):
        self.memory[Word(0x0200)] = Byte(0xA9)
        self.memory[Word(0x0201)] = Byte(0x05)

        self.run_cpu()

        # 2 cycles + 1 for brk
        self.assertEqual(self.clock.cycles, 3)
        self.assertEqual(self.cpu.a, Byte(0x05))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 0])

    def test_lda_zero(self):
        self.memory[Word(0x0200)] = Byte(0xA9)
        self.memory[Word(0x0201)] = Byte(0x00)

        self.run_cpu()

        self.assertEqual(self.clock.cycles, 3)
        self.assertEqual(self.cpu.a, Byte(0x00))
        self.check_flags(self.cpu, [0, 1, 0, 0, 1, 0, 0, 0])

    def test_lda_negative(self):
        self.memory[Word(0x0200)] = Byte(0xA9)
        self.memory[Word(0x0201)] = Byte(0xFF)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 3)
        self.assertEqual(self.cpu.a, Byte(0xFF))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 1])

    def test_lda_zero_page(self):
        self.memory[Word(0x0200)] = Byte(0xA5)
        self.memory[Word(0x0201)] = Byte(0x42)
        self.memory[Word(0x0042)] = Byte(0x05)

        self.run_cpu()

        self.assertEqual(self.clock.cycles, 4)
        self.assertEqual(self.cpu.a, Byte(0x05))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 0])

    def test_lda_zero_page_x(self):
        # LDX 0x05
        self.memory[Word(0x0200)] = Byte(0xA2)
        self.memory[Word(0x0201)] = Byte(0x05)
        # LDA 0x42, X
        self.memory[Word(0x0202)] = Byte(0xB5)
        self.memory[Word(0x0203)] = Byte(0x37)

        self.memory[Word(0x003C)] = Byte(0x43)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 7)
        self.assertEqual(self.cpu.a, Byte(0x43))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 0])

    def test_lda_zero_page_x_wrap(self):
        # LDX 0x05
        self.memory[Word(0x0200)] = Byte(0xA2)
        self.memory[Word(0x0201)] = Byte(0xF2)
        # LDA 0x42, X
        self.memory[Word(0x0202)] = Byte(0xB5)
        self.memory[Word(0x0203)] = Byte(0x37)

        self.memory[Word(0x0029)] = Byte(0x43)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 7)
        self.assertEqual(self.cpu.a, Byte(0x43))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 0])

    def test_lda_absolute(self):
        self.memory[Word(0x0200)] = Byte(0xAD)
        self.memory[Word(0x0201)] = Byte(0xA3)
        self.memory[Word(0x0202)] = Byte(0x25)
        self.memory[Word(0x25A3)] = Byte(0xF2)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 5)
        self.assertEqual(self.cpu.a, Byte(0xF2))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 1])

    def test_lda_absolute_x(self):
        # LDX 0x21
        self.memory[Word(0x0200)] = Byte(0xA2)
        self.memory[Word(0x0201)] = Byte(0x01)
        # LDA 0x259E, X
        self.memory[Word(0x0202)] = Byte(0xBD)
        self.memory[Word(0x0203)] = Byte(0x9E)
        self.memory[Word(0x0204)] = Byte(0x25)
        self.memory[Word(0x259F)] = Byte(0xF2)

        self.run_cpu()

        self.assertEqual(self.clock.cycles, 7)
        self.assertEqual(self.cpu.a, Byte(0xF2))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 1])

    def test_lda_absolute_y(self):
        # LDY 0x21
        self.memory[Word(0x0200)] = Byte(0xA0)
        self.memory[Word(0x0201)] = Byte(0x21)
        # LDA 0x259E, Y
        self.memory[Word(0x0202)] = Byte(0xB9)
        self.memory[Word(0x0203)] = Byte(0x9E)
        self.memory[Word(0x0204)] = Byte(0x25)
        self.memory[Word(0x25BF)] = Byte(0x63)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 7)
        self.assertEqual(self.cpu.a, Byte(0x63))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 0])

    def test_lda_indirect_x(self):
        # LDX 0x52
        self.memory[Word(0x0200)] = Byte(0xA2)
        self.memory[Word(0x0201)] = Byte(0x52)
        # LDA (0x44, X)
        self.memory[Word(0x0202)] = Byte(0xA1)
        self.memory[Word(0x0203)] = Byte(0x44)

        self.memory[Word(0x0096)] = Byte(0x42)
        self.memory[Word(0x0097)] = Byte(0x25)
        self.memory[Word(0x2542)] = Byte(0x00)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 9)
        self.assertEqual(self.cpu.a, Byte(0x00))
        self.check_flags(self.cpu, [0, 1, 0, 0, 1, 0, 0, 0])

    def test_lda_indirect_y(self):
        # LDY 0x52
        self.memory[Word(0x0200)] = Byte(0xA0)
        self.memory[Word(0x0201)] = Byte(0x52)
        # LDA (0x44), Y
        self.memory[Word(0x0202)] = Byte(0xB1)
        self.memory[Word(0x0203)] = Byte(0x44)

        self.memory[Word(0x0044)] = Byte(0x42)
        self.memory[Word(0x0045)] = Byte(0x25)
        self.memory[Word(0x2594)] = Byte(0x01)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 8)
        self.assertEqual(self.cpu.a, Byte(0x01))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 0])

    def test_lda_indirect_y_cross_page(self):
        # LDY 0x52
        self.memory[Word(0x0200)] = Byte(0xA0)
        self.memory[Word(0x0201)] = Byte(0x52)
        # LDA (0x44), Y
        self.memory[Word(0x0202)] = Byte(0xB1)
        self.memory[Word(0x0203)] = Byte(0x44)

        self.memory[Word(0x0044)] = Byte(0xD2)
        self.memory[Word(0x0045)] = Byte(0x25)
        self.memory[Word(0x2624)] = Byte(0x01)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 9)
        self.assertEqual(self.cpu.a, Byte(0x01))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 0])

    def test_ldx(self):
        self.memory[Word(0x0200)] = Byte(0xA2)
        self.memory[Word(0x0201)] = Byte(0x05)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 3)
        self.assertEqual(self.cpu.x, Byte(0x05))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 0])

    def test_ldx_zero_page(self):
        self.memory[Word(0x0200)] = Byte(0xA6)
        self.memory[Word(0x0201)] = Byte(0x00)
        self.memory[Word(0x0000)] = Byte(0xFF)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 4)
        self.assertEqual(self.cpu.x, Byte(0xFF))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 1])

    def test_ldx_zero_page_y(self):
        # LDY 0x05
        self.memory[Word(0x0200)] = Byte(0xA0)
        self.memory[Word(0x0201)] = Byte(0x05)
        # LDX 0x42, Y
        self.memory[Word(0x0202)] = Byte(0xB6)
        self.memory[Word(0x0203)] = Byte(0x37)

        self.memory[Word(0x003C)] = Byte(0x43)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 7)
        self.assertEqual(self.cpu.x, Byte(0x43))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 0])

    def test_ldx_absolute(self):
        self.memory[Word(0x0200)] = Byte(0xAE)
        self.memory[Word(0x0201)] = Byte(0xA9)
        self.memory[Word(0x0202)] = Byte(0x19)
        self.memory[Word(0x19A9)] = Byte(0xF3)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 5)
        self.assertEqual(self.cpu.x, Byte(0xF3))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 1])

    def test_ldx_absolute_y(self):
        # LDY 0xF2
        self.memory[Word(0x0200)] = Byte(0xA0)
        self.memory[Word(0x0201)] = Byte(0x22)
        # LDX 0x259E, Y
        self.memory[Word(0x0202)] = Byte(0xBE)
        self.memory[Word(0x0203)] = Byte(0x9F)
        self.memory[Word(0x0204)] = Byte(0x25)
        self.memory[Word(0x25C1)] = Byte(0x00)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 7)
        self.assertEqual(self.cpu.x, Byte(0x00))
        self.check_flags(self.cpu, [0, 1, 0, 0, 1, 0, 0, 0])

    def test_ldx_absolute_y_page_crossed(self):
        # LDY 0xF2
        self.memory[Word(0x0200)] = Byte(0xA0)
        self.memory[Word(0x0201)] = Byte(0xF2)
        # LDX 0x259E, Y
        self.memory[Word(0x0202)] = Byte(0xBE)
        self.memory[Word(0x0203)] = Byte(0x9F)
        self.memory[Word(0x0204)] = Byte(0x25)
        self.memory[Word(0x2691)] = Byte(0x00)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 8)
        self.assertEqual(self.cpu.x, Byte(0x00))
        self.check_flags(self.cpu, [0, 1, 0, 0, 1, 0, 0, 0])

    def test_ldy(self):
        self.memory[Word(0x0200)] = Byte(0xA0)
        self.memory[Word(0x0201)] = Byte(0x7F)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 3)
        self.assertEqual(self.cpu.y, Byte(0x7F))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 0])

    def test_ldy_zero_page(self):
        self.memory[Word(0x0200)] = Byte(0xA4)
        self.memory[Word(0x0201)] = Byte(0xFF)
        self.memory[Word(0x00FF)] = Byte(0x80)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 4)
        self.assertEqual(self.cpu.y, Byte(0x80))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 1])

    def test_ldy_zero_page_x(self):
        # LDX 0x7F
        self.memory[Word(0x0200)] = Byte(0xA2)
        self.memory[Word(0x0201)] = Byte(0x7F)
        # LDY 0x45, X
        self.memory[Word(0x0202)] = Byte(0xB4)
        self.memory[Word(0x0203)] = Byte(0x45)

        self.memory[Word(0x00C4)] = Byte(0x43)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 7)
        self.assertEqual(self.cpu.y, Byte(0x43))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 0])

    def test_ldy_absolute(self):
        self.memory[Word(0x0200)] = Byte(0xAC)
        self.memory[Word(0x0201)] = Byte(0x9F)
        self.memory[Word(0x0202)] = Byte(0x25)
        self.memory[Word(0x259F)] = Byte(0x0F)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 5)
        self.assertEqual(self.cpu.y, Byte(0x0F))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 0])

    def test_ldy_absolute_x(self):
        # LDX 0x23
        self.memory[Word(0x0200)] = Byte(0xA2)
        self.memory[Word(0x0201)] = Byte(0x23)
        # LDY 0x259E, X
        self.memory[Word(0x0202)] = Byte(0xBC)
        self.memory[Word(0x0203)] = Byte(0x9E)
        self.memory[Word(0x0204)] = Byte(0x25)
        self.memory[Word(0x25C1)] = Byte(0x00)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 7)
        self.assertEqual(self.cpu.y, Byte(0x00))
        self.check_flags(self.cpu, [0, 1, 0, 0, 1, 0, 0, 0])

    def test_ldy_absolute_x_page_crossed(self):
        # LDX 0x0F
        self.memory[Word(0x0200)] = Byte(0xA2)
        self.memory[Word(0x0201)] = Byte(0x0F)
        # LDY 0x259E, X
        self.memory[Word(0x0202)] = Byte(0xBC)
        self.memory[Word(0x0203)] = Byte(0xF2)
        self.memory[Word(0x0204)] = Byte(0x25)
        self.memory[Word(0x2601)] = Byte(0xA0)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 8)
        self.assertEqual(self.cpu.y, Byte(0xA0))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 1])

    def test_lsr(self):
        # LDA 0x85
        self.memory[Word(0x0200)] = Byte(0xA9)
        self.memory[Word(0x0201)] = Byte(0x85)
        # LSR A
        self.memory[Word(0x0202)] = Byte(0x4A)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 5)
        self.assertEqual(self.cpu.a, Byte(0x42))
        self.check_flags(self.cpu, [1, 0, 0, 0, 1, 0, 0, 0])

    def test_lsr_zero(self):
        # LDA 0x01
        self.memory[Word(0x0200)] = Byte(0xA9)
        self.memory[Word(0x0201)] = Byte(0x01)
        # LSR A
        self.memory[Word(0x0202)] = Byte(0x4A)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 5)
        self.assertEqual(self.cpu.a, Byte(0x00))
        self.check_flags(self.cpu, [1, 1, 0, 0, 1, 0, 0, 0])

    def test_lsr_zero_page(self):
        self.memory[Word(0x0200)] = Byte(0x46)
        self.memory[Word(0x0201)] = Byte(0x42)
        self.memory[Word(0x0042)] = Byte(0x57)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 6)
        self.assertEqual(self.memory[Word(0x0042)], Byte(0x2B))
        self.check_flags(self.cpu, [1, 0, 0, 0, 1, 0, 0, 0])

    def test_lsr_zero_page_x(self):
        # LDX 0x05
        self.memory[Word(0x0200)] = Byte(0xA2)
        self.memory[Word(0x0201)] = Byte(0x05)
        # LSR 0x42, X
        self.memory[Word(0x0202)] = Byte(0x56)
        self.memory[Word(0x0203)] = Byte(0x37)

        self.memory[Word(0x003C)] = Byte(0x58)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 9)
        self.assertEqual(self.memory[Word(0x003C)], Byte(0x2C))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 0])

    def test_lsr_absolute(self):
        self.memory[Word(0x0200)] = Byte(0x4E)
        self.memory[Word(0x0201)] = Byte(0xF4)
        self.memory[Word(0x0202)] = Byte(0xA8)
        self.memory[Word(0xA8F4)] = Byte(0xDB)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 7)
        self.assertEqual(self.memory[Word(0xA8F4)], Byte(0x6D))
        self.check_flags(self.cpu, [1, 0, 0, 0, 1, 0, 0, 0])

    def test_lsr_absolute_x(self):
        # LDX 0x05
        self.memory[Word(0x0200)] = Byte(0xA2)
        self.memory[Word(0x0201)] = Byte(0x05)
        # LSR 0x4237, X
        self.memory[Word(0x0202)] = Byte(0x5E)
        self.memory[Word(0x0203)] = Byte(0x37)
        self.memory[Word(0x0204)] = Byte(0x42)
        self.memory[Word(0x423C)] = Byte(0x58)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 10)
        self.assertEqual(self.memory[Word(0x423C)], Byte(0x2C))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 0])

    def test_ora(self):
        # LDA 0x85
        self.memory[Word(0x0200)] = Byte(0xA9)
        self.memory[Word(0x0201)] = Byte(0x85)
        # ORA 0x42
        self.memory[Word(0x0202)] = Byte(0x09)
        self.memory[Word(0x0203)] = Byte(0x42)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 5)
        self.assertEqual(self.cpu.a, Byte(0xC7))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 1])

    def test_ora_zero(self):
        # LDA 0x00
        self.memory[Word(0x0200)] = Byte(0xA9)
        self.memory[Word(0x0201)] = Byte(0x00)
        # ORA 0x00
        self.memory[Word(0x0202)] = Byte(0x09)
        self.memory[Word(0x0203)] = Byte(0x00)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 5)
        self.assertEqual(self.cpu.a, Byte(0x00))
        self.check_flags(self.cpu, [0, 1, 0, 0, 1, 0, 0, 0])

    def test_ora_zero_page(self):
        self.memory[Word(0x0200)] = Byte(0xA9)
        self.memory[Word(0x0201)] = Byte(0xD3)

        self.memory[Word(0x0202)] = Byte(0x05)
        self.memory[Word(0x0203)] = Byte(0x42)
        self.memory[Word(0x0042)] = Byte(0x57)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 6)
        self.assertEqual(self.cpu.a, Byte(0xD7))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 1])

    def test_ora_zero_page_x(self):
        # LDX 0x05
        self.memory[Word(0x0200)] = Byte(0xA2)
        self.memory[Word(0x0201)] = Byte(0x05)
        # LDA 0x56
        self.memory[Word(0x0202)] = Byte(0xA9)
        self.memory[Word(0x0203)] = Byte(0x56)
        # ORA 0x37, X
        self.memory[Word(0x0204)] = Byte(0x15)
        self.memory[Word(0x0205)] = Byte(0x37)

        self.memory[Word(0x003C)] = Byte(0x58)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 9)
        self.assertEqual(self.cpu.a, Byte(0x5E))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 0])

    def test_ora_absolute(self):
        # LDA 0x85
        self.memory[Word(0x0200)] = Byte(0xA9)
        self.memory[Word(0x0201)] = Byte(0x85)
        # ORA 0x5742
        self.memory[Word(0x0202)] = Byte(0x0D)
        self.memory[Word(0x0203)] = Byte(0x42)
        self.memory[Word(0x0204)] = Byte(0x57)
        self.memory[Word(0x5742)] = Byte(0xC3)
        self.run_cpu()

        self.assertEqual(self.clock.cycles, 7)
        self.assertEqual(self.cpu.a, Byte(0xC7))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 1])

    def test_ora_absolute_x(self):
        # LDX 0x05
        self.memory[Word(0x0200)] = Byte(0xA2)
        self.memory[Word(0x0201)] = Byte(0x05)
        # LDA 0x25
        self.memory[Word(0x0202)] = Byte(0xA9)
        self.memory[Word(0x0203)] = Byte(0x25)
        # ORA 0x289E, X
        self.memory[Word(0x0204)] = Byte(0x1D)
        self.memory[Word(0x0205)] = Byte(0x9E)
        self.memory[Word(0x0206)] = Byte(0x25)
        self.memory[Word(0x25A3)] = Byte(0xF2)

        self.run_cpu()

        self.assertEqual(self.clock.cycles, 9)
        self.assertEqual(self.cpu.a, Byte(0xF7))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 1])

    def test_ora_absolute_y_page_crossed(self):
        # LDY 0xD3
        self.memory[Word(0x0200)] = Byte(0xA0)
        self.memory[Word(0x0201)] = Byte(0xD3)
        # LDA 0xA9
        self.memory[Word(0x0202)] = Byte(0xA9)
        self.memory[Word(0x0203)] = Byte(0xA9)
        # ORA 0x2391, Y
        self.memory[Word(0x0204)] = Byte(0x19)
        self.memory[Word(0x0205)] = Byte(0x91)
        self.memory[Word(0x0206)] = Byte(0x23)
        self.memory[Word(0x2464)] = Byte(0xF2)

        self.run_cpu()

        self.assertEqual(self.clock.cycles, 10)
        self.assertEqual(self.cpu.a, Byte(0xFB))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 1])

    def test_ora_indirect_x(self):
        # LDX 0x05
        self.memory[Word(0x0200)] = Byte(0xA2)
        self.memory[Word(0x0201)] = Byte(0x05)
        # LDA 0x25
        self.memory[Word(0x0202)] = Byte(0xA9)
        self.memory[Word(0x0203)] = Byte(0x25)
        # ORA 0x289E, X
        self.memory[Word(0x0204)] = Byte(0x01)
        self.memory[Word(0x0205)] = Byte(0x23)
        self.memory[Word(0x0028)] = Byte(0x25)
        self.memory[Word(0x0029)] = Byte(0x44)
        self.memory[Word(0x4425)] = Byte(0x64)

        self.run_cpu()

        self.assertEqual(self.clock.cycles, 11)
        self.assertEqual(self.cpu.a, Byte(0x65))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 0])

    def test_ora_indirect_y(self):
        # LDY 0x06
        self.memory[Word(0x0200)] = Byte(0xA0)
        self.memory[Word(0x0201)] = Byte(0x06)
        # LDA 0x25
        self.memory[Word(0x0202)] = Byte(0xA9)
        self.memory[Word(0x0203)] = Byte(0x25)
        # ORA 0x289E, Y
        self.memory[Word(0x0204)] = Byte(0x11)
        self.memory[Word(0x0205)] = Byte(0x23)
        self.memory[Word(0x0023)] = Byte(0x25)
        self.memory[Word(0x0024)] = Byte(0x44)
        self.memory[Word(0x442B)] = Byte(0x66)

        self.run_cpu()

        self.assertEqual(self.clock.cycles, 10)
        self.assertEqual(self.cpu.a, Byte(0x67))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 0])

    def test_pha(self):
        # LDA 0xA3
        self.memory[Word(0x0200)] = Byte(0xA9)
        self.memory[Word(0x0201)] = Byte(0xA3)
        # PHA
        self.memory[Word(0x0202)] = Byte(0x48)

        self.run_cpu()

        self.assertEqual(self.clock.cycles, 6)
        self.assertEqual(self.cpu.a, Byte(0xA3))
        self.assertEqual(self.cpu.sp, Byte(0xFE))
        self.assertEqual(self.memory[Word(0x01FF)], Byte(0xA3))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 1])

    def test_pla(self):
        # LDA 0xA3
        self.memory[Word(0x0200)] = Byte(0xA9)
        self.memory[Word(0x0201)] = Byte(0xA3)
        # PHA
        self.memory[Word(0x0202)] = Byte(0x48)
        # LDA 0x01
        self.memory[Word(0x0203)] = Byte(0xA9)
        self.memory[Word(0x0204)] = Byte(0x01)
        # PLA
        self.memory[Word(0x0205)] = Byte(0x68)

        self.run_cpu()

        self.assertEqual(self.clock.cycles, 12)
        self.assertEqual(self.cpu.a, Byte(0xA3))
        self.assertEqual(self.cpu.sp, Byte(0xFF))
        self.assertEqual(self.memory[Word(0x01FF)], Byte(0xA3))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 1])

    def test_php(self):
        # LDA 0xA3
        self.memory[Word(0x0200)] = Byte(0xA9)
        self.memory[Word(0x0201)] = Byte(0xA3)
        # PHP
        self.memory[Word(0x0202)] = Byte(0x08)

        self.run_cpu()

        self.assertEqual(self.clock.cycles, 6)
        self.assertEqual(self.cpu.a, Byte(0xA3))
        self.assertEqual(self.cpu.sp, Byte(0xFE))
        self.assertEqual(self.memory[Word(0x01FF)], Byte(0x80))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 1])

    def test_php_zero(self):
        # LDA 0xA3
        self.memory[Word(0x0200)] = Byte(0xA9)
        self.memory[Word(0x0201)] = Byte(0x00)
        # PHP
        self.memory[Word(0x0202)] = Byte(0x08)

        self.run_cpu()

        self.assertEqual(self.clock.cycles, 6)
        self.assertEqual(self.cpu.a, Byte(0x00))
        self.assertEqual(self.cpu.sp, Byte(0xFE))
        self.assertEqual(self.memory[Word(0x01FF)], Byte(0x02))
        self.check_flags(self.cpu, [0, 1, 0, 0, 1, 0, 0, 0])

    def test_plp(self):
        # LDA 0xA3
        self.memory[Word(0x0200)] = Byte(0xA9)
        self.memory[Word(0x0201)] = Byte(0xA2)
        # PHP
        self.memory[Word(0x0202)] = Byte(0x08)
        # LDA 0x01
        self.memory[Word(0x0203)] = Byte(0xA9)
        self.memory[Word(0x0204)] = Byte(0x01)
        # PLP
        self.memory[Word(0x0205)] = Byte(0x28)

        self.run_cpu()

        self.assertEqual(self.clock.cycles, 12)
        self.assertEqual(self.cpu.a, Byte(0x01))
        self.assertEqual(self.cpu.sp, Byte(0xFF))
        self.assertEqual(self.memory[Word(0x01FF)], Byte(0x80))
        self.check_flags(self.cpu, [0, 0, 0, 0, 1, 0, 0, 1])


if __name__ == '__main__':
    unittest.main()
