#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VEML7700 を使って照度(LUX)を取得するライブラリです．

Usage:
  veml7700.py [-b BUS] [-d DEV_ADDR]

Options:
  -b BUS        : I2C バス番号．[default: 0x01]
  -d DEV_ADDR   : デバイスアドレス(7bit)． [default: 0x10]
"""

import time
import smbus2


class VEML7700:
    NAME = "VEML7700"
    DEV_ADDR = 0x10  # 7bit
    RASP_I2C_BUS = 0x1  # Raspberry Pi の I2C のバス番号

    REG_ALS_CONF = 0x00
    REG_ALS = 0x04

    ALS_GAIN = {
        1: 0x0 << 11,
        2: 0x1 << 11,
        0.125: 0x2 << 11,
        0.25: 0x3 << 11,
    }
    ALS_IT = {
        100: 0x0 << 6,
        200: 0x1 << 6,
        400: 0x2 << 6,
        800: 0x3 << 6,
        50: 0x8 << 6,
        25: 0xC << 6,
    }

    ALS_SD_POWER_ON = 0x00 << 0
    ALS_SD_POWER_OFF = 0x01 << 0

    def __init__(self, bus=RASP_I2C_BUS, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = smbus2.SMBus(bus)
        self.gain = 0.125
        self.integ = 25

    def enable(self):
        value = (
            self.ALS_GAIN[self.gain] | self.ALS_IT[self.integ] | self.ALS_SD_POWER_ON
        )

        self.i2cbus.write_i2c_block_data(
            self.dev_addr,
            self.REG_ALS_CONF,
            [(value >> 0) & 0xFF, (value >> 8) & 0xFF],
        )

    def disable(self):
        value = (
            self.ALS_GAIN[self.gain] | self.ALS_IT[self.integ] | self.ALS_SD_POWER_OFF
        )

        self.i2cbus.write_i2c_block_data(
            self.dev_addr,
            self.REG_ALS_CONF,
            [(value >> 0) & 0xFF, (value >> 8) & 0xFF],
        )

    def set_integ(self, integ):
        self.integ = integ

    def set_gain(self, gain):
        self.gain = gain

    def wait(self):
        time.sleep(self.integ / 1000.0 + 0.1)

    def ping(self):
        try:
            self.i2cbus.read_i2c_block_data(self.dev_addr, self.REG_ALS_CONF, 2)

            # NOTE: 読み出しエラーが起こらなければセンサーが接続されていると見なす
            return True
        except:
            pass

        return False

    def get_value_impl(self):
        self.enable()
        self.wait()

        data = self.i2cbus.read_i2c_block_data(self.dev_addr, self.REG_ALS, 2)

        self.disable()

        als = int.from_bytes(data, byteorder="little")
        als *= 0.0036 * (800 / self.integ) * (2 / self.gain)

        if self.gain == 0.125:
            # NOTE:
            # https://www.vishay.com/docs/84367/designingveml6030.pdf
            als = (
                (6.0135e-13 * als ** 4)
                - (9.3924e-9 * als ** 3)
                + (8.1488e-5 * als ** 2)
                + (1.0023e0 * als)
            )

        return [als]

    def get_value(self):
        value = self.get_value_impl()

        if value[0] < 1000:
            self.set_integ(100)
            return self.get_value_impl()
        else:
            return value

    def get_value_map(self):
        value = self.get_value()

        return {"lux": value[0]}


if __name__ == "__main__":
    # TEST Code
    from docopt import docopt
    import pathlib
    import sys
    import logging

    sys.path.append(str(pathlib.Path(__file__).parent.parent))

    import sensor.veml7700

    args = docopt(__doc__)
    bus = int(args["-b"], 0)
    dev_addr = int(args["-d"], 0)

    logging.getLogger().setLevel(logging.INFO)

    sensor = sensor.veml7700.VEML7700(bus=bus, dev_addr=dev_addr)

    ping = sensor.ping()
    logging.info("PING: {ping}".format(ping=ping))
    if ping:
        logging.info("VALUE: {value}".format(value=sensor.get_value_map()))
