class ByteError(ValueError):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f'ByteError: {self.message}'


class InterruptError(ValueError):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f'InterruptError: {self.message}'


class AddressModeError(ValueError):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f'AddressModeError: {self.message}'
