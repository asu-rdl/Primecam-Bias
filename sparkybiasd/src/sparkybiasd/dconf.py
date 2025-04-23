from omegaconf import OmegaConf, DictConfig


"""
Create the config structure

card1:
  chan1:
    output = false
    wiper = 0
  ...
  chan8:
    output = false
    wiper = 0
...
card18
  chan1:
    output = false
    wiper = 0
  ...
  chan8:
    output = false
   d
"""
def gen() -> DictConfig:
    config = OmegaConf.create()
    for i in range(1,18+1):
        card = f'card{i}'
        config[card] = {}
        for j in range(1, 8+1):
            chan = f"chan{j}"
            config[card][chan] = {"output": True, "wiper": 0}
    return config
