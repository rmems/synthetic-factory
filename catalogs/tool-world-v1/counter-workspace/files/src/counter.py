"""Tiny counter used by the workspace pack."""


class Counter:
    def __init__(self, value=0):
        self._value = int(value)

    def add(self, delta):
        self._value += int(delta)
        return self._value

    def get(self):
        return self._value
