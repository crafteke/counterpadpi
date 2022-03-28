#doc:https://www.auctoris.co.uk/2017/04/29/calling-c-classes-from-python-with-ctypes/
import ctypes
#lib = ctypes.cdll.LoadLibrary('./build/lib.linux-armv7l-3.7/counter.cpython-37m-arm-linux-gn$
lib = ctypes.CDLL('/lib/libwiringPi.so', mode = ctypes.RTLD_GLOBAL)
lib = ctypes.CDLL('./counterPi/build/lib.linux-armv7l-3.7/counter.cpython-37m-arm-linux-gnueabihf.so', mode = ctypes.RTLD_GLOBAL)

class Counter(object):
    def __init__(self):
        lib.counter_new.restype = ctypes.c_void_p
        lib.setup.argtypes = [ctypes.c_void_p, ctypes.c_int,ctypes.c_int,ctypes.c_int]
        lib.setup.restype = ctypes.c_void_p
        lib.display_number.argtypes = [ctypes.c_int]
        lib.display_number.restype = ctypes.c_void_p
        lib.test_led.argtypes=[ctypes.c_void_p]
        lib.test_led.restype=ctypes.c_void_p
        self.obj = lib.counter_new()

    def setup(self,_data_pin,_clock_pin, _latch_pin):
        lib.setup(self.obj,_data_pin, _clock_pin,_latch_pin)

    def display_number(self, val,display_dot):
        return lib.display_number(self.obj, val,display_dot)

    def test_led(self):
        lib.test_led(self.obj)
