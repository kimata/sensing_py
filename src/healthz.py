#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Liveness のチェックを行います

Usage:
  healthz.py [-c CONFIG] [-d]

Options:
  -c CONFIG         : CONFIG を設定ファイルとして読み込んで実行します．[default: config.yaml]
  -d                : デバッグモードで動作します．
"""

from docopt import docopt

import pathlib
import datetime
import logging
import sys

sys.path.append(str(pathlib.Path(__file__).parent.parent / "lib"))

from config import load_config
import logger

args = docopt(__doc__)

config_file = args["-c"]
debug_mode = args["-d"]

if debug_mode:
    log_level = logging.DEBUG
else:
    log_level = logging.INFO

logger.init(
    "hems.sensing_py",
    level=log_level,
)

logging.info("Using config config: {config_file}".format(config_file=config_file))
config = load_config(config_file)

liveness_file = pathlib.Path(config["liveness"]["file"])

if not liveness_file.exists():
    logging.warning("Not executed.")
    sys.exit(-1)

elapsed = datetime.datetime.now() - datetime.datetime.fromtimestamp(
    liveness_file.stat().st_mtime
)
if elapsed.seconds > config["sense"]["interval"]:
    logging.warning(
        "Execution interval is too long. ({elapsed:,} sec)".format(
            elapsed=elapsed.seconds
        )
    )
    sys.exit(-1)

logging.info("OK.")
sys.exit(0)
