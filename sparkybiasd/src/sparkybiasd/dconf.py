from omegaconf import OmegaConf, DictConfig
import os
CONFIGPATH = os.environ.get("HOME", "")+"/daemon/config.yaml"

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
    config_file = OmegaConf.load(CONFIGPATH)
    # values from file are preferred to defaults
    conf = OmegaConf.merge(conf, config_file)
except FileNotFoundError:
    pass

os.makedirs(os.path.dirname(CONFIGPATH), exist_ok=True)
OmegaConf.save(conf, CONFIGPATH)

__all__ = ["conf"]
