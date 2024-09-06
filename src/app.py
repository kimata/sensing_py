#!/usr/bin/env python3
"""
I2C/SPI/UART で接続されたセンサーで計測を行い，結果を Fluentd で送信する
スクリプトです．

Usage:
  app.py [-c CONFIG] [-d]

Options:
  -c CONFIG         : CONFIG を設定ファイルとして読み込んで実行します．[default: config.yaml]
  -d                : デバッグモードで動作します．
"""

import logging
import os
import pathlib
import socket
import time

import my_lib.fluentd_util
import my_lib.footprint
import my_lib.sensor


def execute(config):
    sensor_list = my_lib.sensor.load(config["sensor"])

    active_sensor_list = my_lib.sensor.ping(sensor_list)

    hostname = os.environ.get("NODE_HOSTNAME", socket.gethostname())
    logging.info("Hostname: {hostname}".format(hostname=hostname))

    sender = my_lib.fluentd_util.get_handle("sensor", host=config["fluent"]["host"])

    while True:
        time_start = time.time()
        logging.info("Start.")

        value_map = my_lib.sensor.sense(active_sensor_list)
        value_map.update({"hostname": hostname})

        if my_lib.fluentd_util.send(sender, "rasp", value_map):
            logging.info("Send OK.")
            my_lib.footprint.update(pathlib.Path(config["liveness"]["file"]["sensing"]))

        elapsed_time = time.time() - time_start
        sleep_time = config["sensing"]["interval_sec"] - elapsed_time

        logging.info("Sleep %d sec...", sleep_time)
        time.sleep(sleep_time)


######################################################################
if __name__ == "__main__":
    import docopt
    import my_lib.config
    import my_lib.logger

    args = docopt.docopt(__doc__)

    config_file = args["-c"]
    debug_mode = args["-d"]

    my_lib.logger.init("hems.rasp-shutter", level=logging.DEBUG if debug_mode else logging.INFO)

    logging.info("Using config config: %s", config_file)
    config = my_lib.config.load(config_file)

    execute(config)
