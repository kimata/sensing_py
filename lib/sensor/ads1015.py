#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADS-1015 を使って電圧を計測するライブラリです．

Usage:
  ads1015.py [-b BUS] [-d DEV_ADDR]

Options:
  -b BUS        : I2C バス番号．[default: 0x01]
  -d DEV_ADDR   : デバイスアドレス(7bit)． [default: 0x48]
"""

import smbus2
import time


class ADS1015:
    NAME = "ADS1015"
    DEV_ADDR = 0x48  # 7bit
    RASP_I2C_BUS = 0x1  # Raspberry Pi の I2C のバス番号

    REG_CONFIG = 0x01
    REG_VALUE = 0x00

    REG_CONFIG_FSR_0256 = 5
    REG_CONFIG_FSR_2048 = 2

    REG_CONFIG_MUX_01 = 0
    REG_CONFIG_MUX_0G = 4

    def __init__(self, bus=RASP_I2C_BUS, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = smbus2.SMBus(bus)

        self.mux = self.REG_CONFIG_MUX_01
        self.pga = self.REG_CONFIG_FSR_0256

    def init(self):
        os = 1
        self.i2cbus.i2c_rdwr(
            smbus2.i2c_msg.write(
                self.dev_addr,
                [self.REG_CONFIG, (os << 7) | (self.mux << 4) | (self.pga << 1), 0x03],
            )
        )

    def set_mux(self, mux):
        self.mux = mux

    def set_pga(self, pga):
        self.pga = pga

    def ping(self):
        try:
            read = smbus2.i2c_msg.read(self.dev_addr, 2)
            self.i2cbus.i2c_rdwr(
                smbus2.i2c_msg.write(self.dev_addr, [self.REG_CONFIG]), read
            )

            return bytes(read)[0] != 0
        except:
            return False

    def get_value(self):
        self.init()
        time.sleep(0.1)

        read = smbus2.i2c_msg.read(self.dev_addr, 2)
        self.i2cbus.i2c_rdwr(
            smbus2.i2c_msg.write(self.dev_addr, [self.REG_VALUE]), read
        )

        raw = int.from_bytes(bytes(read), byteorder="big", signed=True)
        if self.pga == self.REG_CONFIG_FSR_0256:
            mvolt = raw * 7.8125 / 1000
        elif self.pga == self.REG_CONFIG_FSR_2048:
            mvolt = raw * 62.5 / 1000

        return [round(mvolt, 3)]

    def get_value_map(self):
        value = self.get_value()

        return {"mvolt": value[0]}


if __name__ == "__main__":
    # TEST Code
    from docopt import docopt
    import pathlib
    import sys
    import pprint

    sys.path.append(str(pathlib.Path(__file__).parent.parent))

    import sensor.ads1015

    args = docopt(__doc__)
    bus = int(args["-b"], 0)
    dev_addr = int(args["-d"], 0)

    ads1015 = sensor.ads1015.ADS1015(bus=bus, dev_addr=dev_addr)

    ping = ads1015.ping()
    print("PING: %s" % ping)

    if ping:
        pprint.pprint(ads1015.get_value_map())
