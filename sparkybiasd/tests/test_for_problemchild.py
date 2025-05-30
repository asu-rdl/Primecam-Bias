import sparkybiasd.hardware as hw
import pytest
import logging

# Configure logging
logging.basicConfig(
    filename='problemchild.log',              # Log file name
    filemode='a',                    # Append mode ('w' for overwrite)
    level=logging.DEBUG,              # Log level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

@pytest.fixture
def hwfixture() -> dict[int, hw.BiasCard]:
    # Enumerate available cards. 
    found_cards = {}
    for i in range(1, 18+1):
        try:
            c = hw.BiasCard(i)
            found_cards[i] = c
        except OSError:
            continue

    logging.info(f"found cards length = {len(found_cards)}")
    logging.info(f"addresses found were {found_cards.keys()}")

    # manually command that all repeaters except 0 disconnect
    for i in range(1, 18):
        try:
            hw.BiasCard.iicBus.write_byte(0x61+i, 0b0_11_00000)
        except OSError:
            continue
    return found_cards


def test_cards_exist(hwfixture):
    assert len(hwfixture) > 0

def test_cardbus_is_disconnected(hwfixture):
    with pytest.raises(OSError):
        hw.BiasCard.iicBus.read_byte(0x27)
        
def test_cardbus_open_and_close(hwfixture):
    card = hwfixture[7]
    card.open()
    hw.BiasCard.iicBus.read_byte(0x27)
    card.close()

    with pytest.raises(OSError):
        hw.BiasCard.iicBus.read_byte(0x27)

def test_enable_channels(hwfixture):
    card = hwfixture[7]
    card.open()
    card.enable_chan(1)
    card.close()

    card = hwfixture[10]
    card.open()
    card.enable_chan(4)
    card.close()
