#!/usr/bin/env python3
"""
EZO-DO を使って pH を取得するライブラリです．

Usage:
  ezo_do.py [-b BUS] [-d DEV_ADDR]

Options:
  -b BUS        : I2C バス番号．[default: 0x01]
  -d DEV_ADDR   : デバイスアドレス(7bit)． [default: 0x4A]
"""

import struct
import time

import smbus2


class EZO_DO:  # noqa: N801
    NAME = "EZO-DO"
    DEV_ADDR = 0x68  # 7bit
    RASP_I2C_BUS = 0x1  # Raspberry Pi の I2C のバス番号

    def __init__(self, bus=RASP_I2C_BUS, dev_addr=DEV_ADDR):  # noqa: D107
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = smbus2.SMBus(bus)

    def ping(self):
        try:
            self.exec_command("i")

            return True
        except Exception:
            return False

    def get_value(self):
        value = self.exec_command("R")

        return round(float(value[1:].decode().rstrip("\x00")), 3)

    def exec_command(self, cmd):
        command = self.__compose_command(cmd.encode())

        self.i2cbus.i2c_rdwr(smbus2.i2c_msg.write(self.dev_addr, command))

        time.sleep(1)

        read = smbus2.i2c_msg.read(self.dev_addr, 10)
        self.i2cbus.i2c_rdwr(read)

        return bytes(read)

    def __compose_command(self, text):
        return list(struct.unpack("B" * len(text), text))

    def get_value_map(self):
        value = self.get_value()

        return {"do": value}


if __name__ == "__main__":
    # TEST Code
    import logging
    import pathlib
    import sys

    from docopt import docopt

    sys.path.append(str(pathlib.Path(__file__).parent.parent))

    import sensor.ezo_do

    args = docopt(__doc__)
    bus = int(args["-b"], 0)
    dev_addr = int(args["-d"], 0)

    logging.getLogger().setLevel(logging.INFO)

    sensor = sensor.ezo_do.EZO_DO(bus=bus, dev_addr=dev_addr)

    ping = sensor.ping()
    logging.info("PING: %s", ping)
    if ping:
        logging.info("VALUE: %s", str(sensor.get_value_map()))
