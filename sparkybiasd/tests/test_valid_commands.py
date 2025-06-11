import pytest
import redis
import json
import os
import redis.exceptions
import time

def txrx_command(redis_fixture, command):
    """Helper function to send a command and receive a response."""
    redis_client, pubsub = redis_fixture
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    return json.loads(message['data'].decode())

@pytest.fixture
def redisFixt():
    """Fixture to create a Redis client."""
    client = redis.Redis(host='10.206.160.58', port=6379)
    psub = client.pubsub()
    psub.subscribe('sparkreply')
    psub.get_message()
    # Ensure the Redis server is running and accessible
    try:
        client.ping()
    except redis.exceptions.ConnectionError:
        pytest.fail("Redis connection failed")
    # Ensure the pubsub is subscribed to the correct channel
    try:
        psub.get_message(timeout=1)  # Wait for a message to ensure subscription is active
    except redis.exceptions.ConnectionError:
        pytest.fail("Redis pubsub subscription failed")
    # Return the client for use in tests
    yield client, psub


def test_redis_connection(redisFixt):
    """Test if the Redis client can connect successfully."""
    redis_client, pubsub = redisFixt
    try:
        redis_client.ping()
    except redis.exceptions.ConnectionError:
        pytest.fail("Redis connection failed")

    
def test_command_get_status(redisFixt):
    """Test the get_status command."""

    # Simulate a command to get status for card 1, channel 1
    command = {
        "command": "getStatus",
        "args": {
            "card": 1,
            "channel": 1
        }
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"
    assert response['card'] == 1, "Expected card 1 in response"
    assert response['channel'] == 1, "Expected channel 1 in response"

def test_enable_output(redisFixt):
    """Test that we set an output."""

    command = {
        "command": "enableOutput",
        "args": {
            "card": 1,
            "channel": 1,
        }
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"

def test_command_seek_voltage(redisFixt):
    """Test that we can seek a voltage."""

    command = {
        "command": "enableOutput",
        "args": {
            "card": 1,
            "channel": 1,
        }
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"

    # Now seek a voltage
    command = {
        "command": "seekVoltage",
        "args": {
            "card": 1,
            "channel": 1,
            "voltage": 0.5
        }
    }

    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"
    assert response['card'] == 1, "Expected card 1 in response"
    assert response['channel'] == 1, "Expected channel 1 in response"

def test_command_disable_output(redisFixt):
    """Test that we can disable an output."""
    command = {
        "command": "disableOutput",
        "args": {
            "card": 1,
            "channel": 1,
        }
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"

def test_command_enable_testload(redisFixt):
    """Test that we can enable a testload."""
    command = {
        "command": "enableTestload",
        "args": {
            "card": 10,
            "channel": 5,
        }
    }

    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"

def test_command_disable_testload(redisFixt):
    """Test that we can enable a testload."""

    command = {
        "command": "disableTestload",
        "args": {
            "card": 10,
            "channel": 5,
        }
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"

def test_command_test_set_channel(redisFixt):
    """
    This is not an automated test, but a manual one.
    A channel is enabled, then a testload is enabled,
    then the channel is set to a voltage, and then the testload
    is disabled. The channel should be at 0V after this. The voltage change should be ovservable
    in the application logs.
    """

    command = {
        "command": "enableOutput",
        "args": {
            "card": 1,
            "channel": 1,
        }
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"

    command["command"] = "enableTestload"
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"

    command["command"] = "seekVoltage"
    command["args"]["voltage"] = 2.0
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"

    command["command"] = "disableTestload"
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"

    command["command"] = "disableOutput"
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"


def test_command_seek_current(redisFixt):
    """Test that we can seek a voltage."""

    # Enable the output first
    command = {
        "command": "enableOutput",
        "args": {
            "card": 10,
            "channel": 3,
        }
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"

    # Enable the testload
    command = {
        "command": "enableTestload",
        "args": {
            "card": 10,
            "channel": 3,
        }
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"


    # Now seek a current
    command = {
        "command": "seekCurrent",
        "args": {
            "card": 10,
            "channel": 3,
            "current": 10
        }
    }

    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"
    assert response['card'] == 10, "Expected card 1 in response"
    assert response['channel'] == 3, "Expected channel 1 in response"
    assert round(response['current']) == 10, "Expected current 10mA in response"
    
    # Disable the testload and output
    command["command"] = "disableTestload"
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"
    command["command"] = "disableOutput"
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"



def test_command_get_cards(redisFixt):
    """Test that we can get the list of cards connected to the bias crate."""
    command = {
        "command": "getAvailableCards",
        "args": {}
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"
    assert response['cards'] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "Expected cards 1-10 in response; big uh oh if this fails"


def test_command_save_configuration(redisFixt):
    """Test that we can save the current configuration."""

    # First enable one output for every card
    for i in range(1, 10+1):
        command = {
            "command": "enableOutput",
            "args": {
                "card": i,
                "channel": 1,
            }
        }
        response = txrx_command(redisFixt, command)
        assert response['status'] == 'success', f"Expected success status in response for card {i}"
    

    command = {
        "command": "saveConfig",
        "args": {}
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"


def test_command_load_configuration(redisFixt):
    """Test that we can load the current configuration."""
    
    # First well disable all of the outputs.

    command = {
        "command": "disableAllOutputs",
        "args": {}
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"

    # Now load the config
    command = {
        "command": "loadConfig",
        "args": {"enableOutputs": True, 
                 "createNewConfig": False}  # This should enable all outputs that were saved
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"

    # Check that all outputs are enabled

    for i in range(1, 10+1):
        command = {
            "command": "getStatus",
            "args": {
                "card": i,
                "channel": 1
            }
        }
        response = txrx_command(redisFixt, command)
        assert response['status'] == 'success', f"Expected success status in response for card {i}"
        assert response['outputEnabled'] == True, f"Expected output on card {i} to be enabled"
    

def test_command_load_configuration_disable_outputs(redisFixt):
    """Test that we can load the current configuration."""
    
    # First well disable all of the outputs.

    command = {
        "command": "disableAllOutputs",
        "args": {}
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"

    # Now load the config
    command = {
        "command": "loadConfig",
        "args": {"enableOutputs": False, 
                 "createNewConfig": False}  # This should enable all outputs that were saved
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"

    # Check that all outputs are enabled

    for i in range(1, 10+1):
        command = {
            "command": "getStatus",
            "args": {
                "card": i,
                "channel": 1
            }
        }
        response = txrx_command(redisFixt, command)
        assert response['status'] == 'success', f"Expected success status in response for card {i}"
        assert response['outputEnabled'] == False, f"Expected output on card {i} to be enabled"
    
    
    




