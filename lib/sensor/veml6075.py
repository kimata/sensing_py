#!/usr/bin/env python3
"""
VEML6075 を使って紫外線を計測するライブラリです．

Usage:
  veml6075.py [-b BUS] [-d DEV_ADDR]

Options:
  -b BUS        : I2C バス番号．[default: 0x01]
  -d DEV_ADDR   : デバイスアドレス(7bit)． [default: 0x10]
"""

import time

import smbus2


class VEML6075:
    NAME = "VEML6075"
    DEV_ADDR = 0x10  # 7bit
    RASP_I2C_BUS = 0x1  # Raspberry Pi の I2C のバス番号

    REG_UV_CONF = 0x00
    REG_UVA = 0x07
    REG_UVB = 0x09
    REG_UVCOMP1 = 0x0A
    REG_UVCOMP2 = 0x0B
    REG_DEVID = 0x0C

    CONF_IT_50MS = 0 << 4
    CONF_IT_100MS = 1 << 4

    CONF_AF_ENABLE = 1 << 1
    CONF_AF_DISABLE = 0 << 1

    CONF_TRIG_ONE = 1 << 2
    CONF_TRIG_NO = 0 << 2

    CONF_SD_POWERON = 0 << 0
    CONF_SD_SHUTDOWN = 1 << 0

    # designingveml6075.pdf
    # For responsivity without a diffusor and IT = 100 ms:
    # UVA sensing resolution of 0.01 UVI = 9 counts
    # UVB sensing resolution of 0.01 UVI = 8 counts
    UVA_RESP_50MS = (0.01 / 9) / 0.5016286645  # From SparkFun_VEML6075_Arduino_Library.cpp
    UVA_RESP_100MS = 0.01 / 9

    UVB_RESP_50MS = (0.01 / 8) / 0.5016286645  # From SparkFun_VEML6075_Arduino_Library.cpp
    UVB_RESP_100MS = 0.01 / 8

    def __init__(self, bus=RASP_I2C_BUS, dev_addr=DEV_ADDR):  # noqa: D107
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = smbus2.SMBus(bus)
        self.it = self.CONF_IT_50MS
        self.is_init = False

    def init(self):
        self.disable()
        self.is_init = True

    def enable(self):
        self.i2cbus.write_i2c_block_data(
            self.dev_addr,
            self.REG_UV_CONF,
            [
                self.it | self.CONF_TRIG_ONE | self.CONF_AF_ENABLE | self.CONF_SD_POWERON,
                0x00,
            ],
        )
        time.sleep(1.1)

    def disable(self):
        self.i2cbus.write_i2c_block_data(
            self.dev_addr,
            self.REG_UV_CONF,
            [
                self.it | self.CONF_AF_ENABLE | self.CONF_SD_SHUTDOWN,
                0x00,
            ],
        )

    def ping(self):
        try:
            data = self.i2cbus.read_i2c_block_data(self.dev_addr, self.REG_DEVID, 2)

            return int.from_bytes(data, byteorder="little") == 0x26
        except Exception:
            return False

    def get_value(self):
        if not self.is_init:
            self.init()

        self.enable()

        data = self.i2cbus.read_i2c_block_data(self.dev_addr, self.REG_UVA, 2)
        uva = int.from_bytes(data, byteorder="little")

        data = self.i2cbus.read_i2c_block_data(self.dev_addr, self.REG_UVB, 2)
        uvb = int.from_bytes(data, byteorder="little")

        data = self.i2cbus.read_i2c_block_data(self.dev_addr, self.REG_UVCOMP1, 2)
        uvcomp1 = int.from_bytes(data, byteorder="little")

        data = self.i2cbus.read_i2c_block_data(self.dev_addr, self.REG_UVCOMP2, 2)
        uvcomp2 = int.from_bytes(data, byteorder="little")

        self.disable()

        uva_calc = uva - ((2.22 * 1.0 * uvcomp1) / 1.0) - ((1.33 * 1.0 * uvcomp2) / 1.0)
        uvb_calc = uvb - ((2.95 * 1.0 * uvcomp1) / 1.0) - ((1.75 * 1.0 * uvcomp2) / 1.0)

        if self.it == self.CONF_IT_50MS:
            uvi = ((uva_calc * self.UVA_RESP_50MS) + (uvb_calc * self.UVB_RESP_50MS)) / 2
        else:
            uvi = ((uva_calc * self.UVA_RESP_100MS) + (uvb_calc * self.UVB_RESP_100MS)) / 2

        uvi = ((uva_calc * 0.001461) + (uvb_calc * 0.002591)) / 2

        return [round(uva_calc, 2), round(uvb_calc, 1), round(uvi, 1)]

    def get_value_map(self):
        value = self.get_value()

        return {
            "uva": value[0],
            "uvb": value[1],
            "uvi": value[2],
        }


if __name__ == "__main__":
    # TEST Code
    import logging
    import pathlib
    import sys

    from docopt import docopt

    sys.path.append(str(pathlib.Path(__file__).parent.parent))

    import sensor.veml6075

    args = docopt(__doc__)
    bus = int(args["-b"], 0)
    dev_addr = int(args["-d"], 0)

    logging.getLogger().setLevel(logging.INFO)

    sensor = sensor.veml6075.VEML6075(bus=bus, dev_addr=dev_addr)

    ping = sensor.ping()
    logging.info("PING: %s", ping)
    if ping:
        logging.info("VALUE: %s", str(sensor.get_value_map()))
