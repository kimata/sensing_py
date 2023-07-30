#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
I2C/SPI/UART で接続されたセンサーで計測を行い，結果を Fluentd で送信する
スクリプトです．

Usage:
  app.py [-c CONFIG]

Options:
  -c CONFIG         : CONFIG を設定ファイルとして読み込んで実行します．[default: config.yaml]
"""

from docopt import docopt

import os
import socket
import sys
import time
import pathlib
import importlib
import logging
import traceback
import fluent.sender

sys.path.append(str(pathlib.Path(__file__).parent.parent / "lib"))

RASP_I2C_BUS = {
    "arm": 0x1,  # Raspberry Pi のデフォルトの I2C バス番号
    "vc": 0x0,  # dtparam=i2c_vc=on で有効化される I2C のバス番号
}


def load_sensor(sensor_cand_list):
    sensor_list = []
    for sensor in sensor_cand_list:
        logging.info("Load {name}".format(name=sensor["name"]))
        mod = importlib.import_module("sensor." + sensor["name"])

        if "i2c_bus" in sensor:
            bus = RASP_I2C_BUS[sensor["i2c_bus"]]

            i2c_dev_file = pathlib.Path("/dev/i2c-{bus}".format(bus=bus))
            if not i2c_dev_file.exists():
                logging.warning(
                    "I2C bus {bus} ({dev_file}) does NOT exist. skipping...".format(
                        bus=bus, dev_file=str(i2c_dev_file)
                    )
                )
                continue

            sensor = getattr(mod, sensor["name"].upper())(bus=bus)
        else:
            sensor = getattr(mod, sensor["name"].upper())()

        sensor_list.append(sensor)

    return sensor_list


def sense(sensor_list):
    value_map = {}
    for sensor in sensor_list:
        try:
            logging.info("Measurement is taken using {name}".format(name=sensor.NAME))
            val = sensor.get_value_map()
            logging.info(val)
            value_map.update(val)
        except:
            logging.error(traceback.format_exc())

    logging.info("Mearged measurements: {result}".format(result=str(value_map)))

    return value_map


def sensor_info(sensor):
    if sensor.dev_addr != None:
        return "{name} (0x{dev_addr:02X})".format(
            name=sensor.NAME, dev_addr=sensor.dev_addr
        )
    else:
        return "{name} ({dev_type})".format(name=sensor.NAME, dev_type=sensor.dev_type)


######################################################################
if __name__ == "__main__":
    from config import load_config
    import logger

    args = docopt(__doc__)

    config_file = args["-c"]

    logger.init("sensor.enviorment", level=logging.INFO)

    logging.info("Load config...")
    config = load_config(config_file)

    logging.info("Load sensors...")
    sensor_list = load_sensor(config["sensor"])

    logging.info("Check sensor existences...")
    sensor_list = list(filter(lambda sensor: sensor.ping(), sensor_list))

    logging.info(
        "Active sensor list: {sensor_list}".format(
            sensor_list=", ".join(map(lambda sensor: sensor_info(sensor), sensor_list))
        )
    )

    hostname = os.environ.get("NODE_HOSTNAME", socket.gethostname())

    logging.info("Hostname: {hostname}".format(hostname=hostname))

    sender = fluent.sender.FluentSender("sensor", host=config["fluent"]["host"])

    while True:
        logging.info("Start.")

        value_map = sense(sensor_list)
        value_map.update({"hostname": hostname})

        if sender.emit("rasp", value_map):
            logging.info("Finish.")
            pathlib.Path(config["liveness"]["file"]).touch()
        else:
            logging.error(sender.last_error)

        logging.info(
            "sleep {sleep_time} sec...".format(sleep_time=config["sense"]["interval"])
        )
        time.sleep(config["sense"]["interval"])
