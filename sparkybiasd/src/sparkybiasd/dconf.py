from omegaconf import OmegaConf, DictConfig
import os
import logging
logger = logging.getLogger(__name__)

CONFIGPATH = os.environ.get("HOME", "")+"/daemon/"
USERHOME = os.environ.get("HOME", "")
APPDATA_PATH = USERHOME+"/daemon/"
LOGPATH = USERHOME+"/daemon/logs/"

os.makedirs(APPDATA_PATH, exist_ok=True)
os.makedirs(LOGPATH, exist_ok=True)
os.makedirs(os.path.dirname(CONFIGPATH), exist_ok=True)

conf = OmegaConf.create()

conf.loglevel = 20 # 10 is DEBUG, 20 is INFO, 30 is WARNING, 40 is ERROR, 50 is CRITICAL
conf["redis"] = {
    "ip": "10.206.160.58",
    "port": 6379,
    "commandChannel": "sparkommand",
    "replyChannel": "sparkreply",
    "keyPrefix": "",
}
conf.biasCards = {}
for i in range(1, 18 + 1):
    card = f"card{i}"
    conf.biasCards[card] = {}
    for j in range(1, 8 + 1):
        chan = f"chan{j}"
        conf.biasCards[card][chan] = {"output": False, "wiper": 0}
try:
    config_file = OmegaConf.load(CONFIGPATH+"config.yaml")
    # values from file are preferred to defaults
    conf = OmegaConf.merge(conf, config_file)
except FileNotFoundError:
    logger.warning("Configuration file not found, using defaults.")
    pass

OmegaConf.save(conf, CONFIGPATH+"config.yaml")

__all__ = ["conf", "CONFIGPATH", "USERHOME", "APPDATA_PATH", "LOGPATH"]
