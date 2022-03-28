import ctypes
#lib = ctypes.cdll.LoadLibrary('./build/lib.linux-armv7l-3.7/counter.cpython-37m-arm-linux-gn$
lib = ctypes.CDLL('/lib/libwiringPi.so', mode = ctypes.RTLD_GLOBAL)
lib = ctypes.CDLL('./counterPi/build/lib.linux-armv7l-3.7/counter.cpython-37m-arm-linux-gnueabihf.so', mode = ctypes.RTLD_GLOBAL)
