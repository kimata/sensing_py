#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Groove 水質測定センサー を使って TDS を取得するライブラリです．

Usage:
  grove_tds.py [-b BUS] [-d DEV_ADDR]

Options:
  -b BUS        : I2C バス番号．[default: 0x01]
  -d DEV_ADDR   : デバイスアドレス(7bit)． [default: 0x4A]
"""

import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent))

import sensor.ads1015


class GROVE_TDS:
    NAME = "GROVE-TDS"
    DEV_ADDR = 0x4A  # 7bit
    RASP_I2C_BUS = 0x1  # Raspberry Pi の I2C のバス番号

    def __init__(self, bus=RASP_I2C_BUS, dev_addr=DEV_ADDR):
        self.dev_addr = dev_addr
        self.adc = sensor.ads1015.ADS1015(bus, dev_addr)
        self.adc.set_mux(self.adc.REG_CONFIG_MUX_0G)
        self.adc.set_pga(self.adc.REG_CONFIG_FSR_2048)

    def ping(self):
        return self.adc.ping()

    def get_value(self, temp=25.0):
        volt = self.adc.get_value()[0] / 1000.0
        tds = (133.42 * volt * volt * volt - 255.86 * volt * volt + 857.39 * volt) * 0.5
        tds /= 1 + 0.018 * (temp - 25)  # 0.018 は実測データから算出

        return [round(tds, 3)]

    def get_value_map(self, temp=25.0):
        value = self.get_value(temp)

        return {"tds": value[0]}


if __name__ == "__main__":
    # TEST Code
    from docopt import docopt
    import pathlib
    import sys
    import logging

    sys.path.append(str(pathlib.Path(__file__).parent.parent))

    import sensor.grove_tds

    args = docopt(__doc__)
    bus = int(args["-b"], 0)
    dev_addr = int(args["-d"], 0)

    logging.getLogger().setLevel(logging.INFO)

    sensor = sensor.grove_tds.GROVE_TDS(bus=bus, dev_addr=dev_addr)

    ping = sensor.ping()
    logging.info("PING: {ping}".format(ping=ping))
    if ping:
        logging.info("VALUE: {value}".format(value=sensor.get_value_map()))
