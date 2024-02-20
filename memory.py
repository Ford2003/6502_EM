from abc import ABC, abstractmethod
from data_types import Word, Byte


class Memory(ABC):
    def __init__(self, memory_size):
        self.memory_size = memory_size
        self.memory = [Byte(0)] * memory_size

    @abstractmethod
    def read(self, address: int):
        pass

    def __len__(self):
        return self.memory_size

    def __getitem__(self, address: int):
        return self.memory[address]

    def __setitem__(self, key, value):
        raise NotImplementedError('Memory is read-only')


class RAM(Memory):
    """Read/write random access memory."""
    def write(self, address: Word, value: Byte):
        self.memory[address] = value

    def read(self, address: Word):
        return self.memory[address]

    def __setitem__(self, address: Word, value: Byte):
        self.memory[address] = value


class RAM64K(RAM):
    """
    65535 bytes of read/write random access memory.

    Maximum addressable memory size is 0xFFFF + 1 bytes.

    Addresses are 16-bit wide.
    """
    def __init__(self):
        super().__init__(0xFFFF + 1)


class ROM(Memory):
    """Read-only memory."""
    def __init__(self, memory_size: int, data):
        super().__init__(memory_size)
        self.data = data

    def read(self, address: Word):
        return self.data[address]


