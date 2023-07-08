#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# APDS-9250 を使って照度を取得するライブラリです．

import struct
import smbus2


class APDS9250:
    NAME = "APDS9250"
    DEV_ADDR = 0x52  # 7bit
    RASP_I2C_BUS = 0x1  # Raspberry Pi の I2C のバス番号

    def __init__(self, bus=RASP_I2C_BUS, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = smbus2.SMBus(bus)

    def ping(self):
        try:
            data = self.i2cbus.read_byte_data(self.dev_addr, 0x06)
            if (data & 0xF0) == 0xB0:
                return True
            else:
                return False
        except:
            return False

    def get_value(self):
        # Resolution = 20bit/400ms, Rate = 1000ms
        self.i2cbus.write_byte_data(self.dev_addr, 0x04, 0x05)
        # Gain = 1
        self.i2cbus.write_byte_data(self.dev_addr, 0x05, 0x01)
        # Sensor = active
        self.i2cbus.write_byte_data(self.dev_addr, 0x00, 0x02)

        data = self.i2cbus.read_i2c_block_data(self.dev_addr, 0x0A, 6)
        ir = struct.unpack("<I", bytes(data[0:3]) + b"\x00")[0]
        als = struct.unpack("<I", bytes(data[3:6]) + b"\x00")[0]

        if als > ir:
            return als * 46.0 / 400
        else:
            return als * 35.0 / 400

    def get_value_map(self):
        value = self.get_value()

        return {"lux": value}


if __name__ == "__main__":
    # TEST Code
    import os
    import sys
    import pprint

    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

    import sensor.apds9250

    apds9250 = sensor.apds9250.APDS9250()

    ping = apds9250.ping()
    print("PING: %s" % ping)

    if ping:
        pprint.pprint(apds9250.get_value_map())
