import sparkybiasd
import time
import pytest

@pytest.fixture
def cfixt():
    crate = sparkybiasd.BiasCrate()
    crate.disable_all_outputs(True)
    return crate

def test_enable_all_outputs(cfixt):
    crate = cfixt
    crate.enable_all_outputs()
    time.sleep(10)

def test_disable_all_outputs(cfixt):
    crate = cfixt
    crate.disable_all_outputs()



    

