#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SHT-35 を使って温度や湿度を取得するライブラリです．
#
# 作成時に使用したのは，Tindie の
# 「SHT35-D (Digital) Humidity & Temperature Sensor」．
# https://www.tindie.com/products/closedcube/sht35-d-digital-humidity-temperature-sensor/

import time
import smbus2


class SHT35:
    NAME = "SHT-35"
    DEV_ADDR = 0x44  # 7bit
    RASP_I2C_BUS = 0x1  # Raspberry Pi の I2C のバス番号

    def __init__(self, bus=RASP_I2C_BUS, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = smbus2.SMBus(bus)
        self.is_init = False

    def init(self):
        # periodic, 1mps, repeatability high
        self.i2cbus.write_byte_data(self.dev_addr, 0x21, 0x30)
        self.is_init = True
        time.sleep(0.01)

    def crc(self, data):
        crc = 0xFF
        for s in data:
            crc ^= s
            for i in range(8):
                if crc & 0x80:
                    crc <<= 1
                    crc ^= 0x131
                else:
                    crc <<= 1
        return crc

    def ping(self):
        try:
            self.i2cbus.write_byte_data(self.dev_addr, 0xF3, 0x2D)
            data = self.i2cbus.read_i2c_block_data(self.dev_addr, 0x00, 3)

            return self.crc(data[0:2]) == data[2]
        except:
            return False

    def get_value(self):
        if not self.is_init:
            self.init()

        self.i2cbus.write_byte_data(self.dev_addr, 0xE0, 0x00)

        data = self.i2cbus.read_i2c_block_data(self.dev_addr, 0x00, 6)

        if (self.crc(data[0:2]) != data[2]) or (self.crc(data[3:5]) != data[5]):
            raise IOError("ERROR: CRC unmatch.")

        temp = -45 + (175 * int.from_bytes(data[0:2], byteorder="big")) / float(
            2 ** 16 - 1
        )
        humi = 100 * int.from_bytes(data[3:5], byteorder="big") / float(2 ** 16 - 1)

        return [round(temp, 2), round(humi, 2)]

    def get_value_map(self):
        value = self.get_value()

        return {"temp": value[0], "humi": value[1]}


if __name__ == "__main__":
    # TEST Code
    import os
    import sys
    import pprint

    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

    import sensor.sht35

    sht35 = sensor.sht35.SHT35()

    ping = sht35.ping()
    print("PING: %s" % ping)

    if ping:
        pprint.pprint(sht35.get_value_map())
