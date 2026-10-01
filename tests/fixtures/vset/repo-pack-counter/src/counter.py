"""Tiny hardware-independent counter used by VSET oracle fixtures."""


class Counter:
    def __init__(self, value: int = 0) -> None:
        self._value = int(value)

    def add(self, delta: int) -> int:
        self._value += int(delta)
        return self._value

    def get(self) -> int:
        return self._value
