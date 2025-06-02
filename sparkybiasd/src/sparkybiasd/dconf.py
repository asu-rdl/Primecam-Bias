from omegaconf import OmegaConf, DictConfig

CONFIGPATH="/home/asu/daemon/config.yml"

conf = OmegaConf.create()
conf['redis'] = {
  'ip': "10.206.160.58",
  'port':6379,
  'commandChannel' : "sparkommand",
  'replyChannel': "sparkreply",
  'keyPrefix' : ''
}
conf.biasCards = {}
for i in range(1,18+1):
    card = f"card{i}"
    conf.biasCards[card] = {}
    for j in range(1, 8+1):
        chan = f"chan{j}"
        conf.biasCards[card][chan] = {"output": True, "wiper": 0}
try:
  config_file = OmegaConf.load(CONFIGPATH)
  # values from file are preferred to defaults
  conf = OmegaConf.merge(conf, config_file)
except FileNotFoundError:
  pass

OmegaConf.save(conf, CONFIGPATH)

__all__ = [
  'conf'
]
