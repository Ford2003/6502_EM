class DType:
    min_value = float('-inf')
    max_value = float('inf')

    def __init__(self, value):
        if value < self.min_value or value > self.max_value:
            raise ValueError(f'Value must be between {self.min_value} and {self.max_value}, got {value}')
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if new_value < self.min_value or new_value > self.max_value:
            raise ValueError(f'Value must be between {self.min_value} and {self.max_value}, got {new_value}')
        self._value = new_value

    def bin(self):
        return bin(self.value)

    def hex(self):
        return hex(self.value)

    def msb(self):
        return int(bin(self.value)[2])

    def lsb(self):
        return self.value & 1

    def __index__(self):
        return self.value

    def __add__(self, other):
        if isinstance(other, DType):
            return self.__class__(self.value + other.value)
        if isinstance(other, int):
            return self.__class__(self.value + other)
        raise TypeError(f'unsupported operand type(s) for +: {self.__class__.__name__} and {other.__class__.__name__}')

    def __str__(self):
        return f'{self.__class__.__name__}({self.value} | {bin(self)} | {hex(self)})'

    def __rshift__(self, other):
        if isinstance(other, int):
            return self.__class__(self.value >> other)
        raise TypeError(f'unsupported operand type(s) for >>: {self.__class__.__name__}')

    def __lshift__(self, other):
        if isinstance(other, int):
            return self.__class__(self.value << other)
        raise TypeError(f'unsupported operand type(s) for <<: {self.__class__.__name__}')

    def __and__(self, other):
        if isinstance(other, DType):
            return self.__class__(self.value & other.value)
        if isinstance(other, int):
            return self.__class__(self.value & other)
        raise TypeError(f'unsupported operand type(s) for &: {other.__class__.__name__}')

    def __or__(self, other):
        if isinstance(other, DType):
            return self.__class__(self.value | other.value)
        if isinstance(other, int):
            return self.__class__(self.value | other)
        raise TypeError(f'unsupported operand type(s) for |: {other.__class__.__name__}')

    def __xor__(self, other):
        if isinstance(other, DType):
            return self.__class__(self.value ^ other.value)
        if isinstance(other, int):
            return self.__class__(self.value ^ other)
        raise TypeError(f'unsupported operand type(s) for ^: {other.__class__.__name__}')

    def __invert__(self):
        return self.__class__(~self.value)

    def __eq__(self, other):
        if isinstance(other, DType):
            return Bit(self.value == other.value)
        if isinstance(other, int):
            return Bit(self.value == other)
        raise TypeError(f'unsupported operand type(s) for ==: {other.__class__.__name__}')


class Bit(DType):
    max_value = 1
    min_value = 0


class Byte(DType):
    max_value = 0xFF
    min_value = 0


class Word(DType):
    max_value = 0xFFFF
    min_value = 0
