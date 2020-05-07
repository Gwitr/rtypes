import rtypes
from typing import *

# Note: functions don't have type checking yet

class Main(rtypes.TypedObject):
    x: int
    y: Any
    z: List[str]
    w: Callable[[rtypes.TypedObject, int], int]

    __init__: Callable
    def __init__(self):
        self.x = 0
        self.w = self.square
        self.z = rtypes.ListType(str)

    tick: Callable
    def tick(self):
        self.z.append(str(self.w(self.x)))
        self.x += 1
        print(self.z)

    square: Callable
    def square(self: rtypes.TypedObject, x: int) -> int:
        return x ** 2

# Testing the Main() class
x = Main()
for _ in range(10):
    x.tick()

# Testing type checking
x.y = "abc"
x.y = 501.7
x.y = b"Hello"

x.x = 10

x.x = "abc"  # Will raise an error
