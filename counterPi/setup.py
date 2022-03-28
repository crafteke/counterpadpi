from distutils.core import setup, Extension

module1 = Extension('counter',
                    sources = ['displayDriver.cpp'])

setup (name = 'CountDown',
       version = '1.0',
       description = 'Control 7seg display from python',
       headers=['/lib/libwiringPi.so'],
       ext_modules = [module1])
