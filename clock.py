import threading
from time import sleep


class Clock:
    def __init__(self, frequency: int):
        if not isinstance(frequency, int) or frequency <= 0:
            raise ValueError('Frequency must be a positive integer.')

        self.frequency = frequency
        self.period = 1 / frequency
        self.half_period = self.period / 2
        self.cycles = -1

        self._clock_thread = threading.Thread(target=self.run)

        self._clock_high = threading.Event()
        self._clock_low = threading.Event()
        self.clock_activated = threading.Event()

    def start(self):
        self._clock_thread.start()

    def run(self):
        self.clock_activated.set()
        while self.clock_activated.is_set():
            self._clock_high.set()
            self._clock_low.clear()
            self.cycles += 1
            sleep(self.half_period)

            self._clock_high.clear()
            self._clock_low.set()
            sleep(self.half_period)

    def schedule(self, func, *args, **kwargs):
        self._clock_high.wait()
        return func(*args, **kwargs)

    def wait_for_pulse(self):
        if self._clock_high.is_set():
            self._clock_low.wait()

        self._clock_high.wait()

    def stop(self):
        self.clock_activated.clear()


class Clock1Hz(Clock):
    """1Hz clock. 1 cycle per second. 1-second period."""
    def __init__(self):
        super().__init__(1)
