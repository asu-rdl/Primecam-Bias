import pytest
import redis
import json
import os
import redis.exceptions
import time


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

def txrx_command(redis_fixture, command):
    """Helper function to send a command and receive a response."""
    redis_client, pubsub = redis_fixture
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    return json.loads(message['data'].decode())


def test_redis_connection(redisFixt):
    """Test if the Redis client can connect successfully."""
    redis_client, pubsub = redisFixt
    try:
        redis_client.ping()
    except redis.exceptions.ConnectionError:
        pytest.fail("Redis connection failed")

    

def test_command_Nonsense(redisFixt):
    redis_client, pubsub = redisFixt
    command = "Aperture Science, we do what we must because we \ncan for the good of all of us. Except the ones who are dead."


    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)

    response = json.loads(message['data'].decode())
    assert response['status'] == 'error', "Expected error status in response"

def test_command_bad_command(redisFixt):
    """Test that an erroneous command returns an error."""
    redis_client, pubsub = redisFixt

    command = {
        "command": "FailHardFailOften",
        "args": {
            "card": 10,
            "channel": 1
        }
    }

    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'error', "Expected error status in response"

def test_command_has_bad_args_card(redisFixt):
    """Test that a legitimate command with bad arguments returns an error."""
    redis_client, pubsub = redisFixt
    command = {
        "command": "getStatus",
        "args": {
            "card": 100,  # Invalid card number
            "channel": 1
        }
    }
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'error', "Expected error status in response for invalid card"


def test_command_has_bad_args_channel(redisFixt):
    """Test that a legitimate command with bad arguments returns an error."""
    redis_client, pubsub = redisFixt
    command = {
        "command": "getStatus",
        "args": {
            "card": 3,  # Valid Card Number
            "channel": 100  # Invalid channel number
        }
    }
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'error', "Expected error status in response for invalid card"

def test_command_getStatus_on_valid_but_missing_card(redisFixt):
    """Test that a getStatus command on a valid but missing card returns an error."""
    redis_client, pubsub = redisFixt
    command = {
        "command": "getStatus",
        "args": {
            "card": 15,  # Valid Card Number
            "channel": 1
        }
    }
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'error', "Expected error status in response for valid but missing card"


def test_command_getcards_with_args(redisFixt):
    """Test that we can get the list of cards connected to the bias crate."""
    command = {
        "command": "getAvailableCards",
        "args": {"ruhroh": "this is not a valid argument"} #should be ignored
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"
    assert response['cards'] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "Expected cards 1-10 in response; big uh oh if this fails"


def test_seek_impossible_current(redisFixt):
    """Test that we cannot seek an impossible current."""
    # Enable the output first
    command = {
        "command": "enableOutput",
        "args": {
            "card": 4,
            "channel": 3,
        }
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"

    # Now seek an impossible current
    command = {
        "command": "seekCurrent",
        "args": {
            "card": 4,
            "channel": 3,
            "current": 1000  # Impossible current
        }
    }

    response = txrx_command(redisFixt, command)
    assert response['status'] == 'error', "Expected error status in response for impossible current"
    
    # Disable the output
    command["command"] = "disableOutput"
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"


def test_seek_impossible_voltage(redisFixt):
    """Test that we cannot seek an impossible voltage."""
    # Enable the output first
    command = {
        "command": "enableOutput",
        "args": {
            "card": 4,
            "channel": 3,
        }
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"

    command = {
        "command": "seekVoltage",
        "args": {
            "card": 4,
            "channel": 3,
            "voltage": 1000  # Impossible voltage
        }
    }

    response = txrx_command(redisFixt, command)
    assert response['status'] == 'error', "Expected error status in response for impossible voltage"
    
    # Disable the output
    command["command"] = "disableOutput"
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'success', "Expected success status in response"


def test_seek_voltage_invalid_card(redisFixt):
    """Test seeking voltage on an invalid card."""
    # Enable the output first
    command = {
        "command": "enableOutput",
        "args": {
            "card": 40,
            "channel": 3,
        }
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'error', "Expected error status in response"

    # Now seek a voltage on an invalid card
    command = {
        "command": "seekVoltage",
        "args": {
            "card": 40,
            "channel": 3,
            "voltage": 1  # Impossible current
        }
    }

    response = txrx_command(redisFixt, command)
    assert response['status'] == 'error', "Expected error status in response for invalid card"
    
    # Disable the output
    command["command"] = "disableOutput"
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'error', "Expected error status in response"


def test_seek_current_invalid_card(redisFixt):
    """Test seeking current on an invalid card."""
    # Enable the output first
    command = {
        "command": "enableOutput",
        "args": {
            "card": 40,
            "channel": 3,
        }
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'error', "Expected error status in response"

    # Now seek a current on an invalid card
    command = {
        "command": "seekCurrent",
        "args": {
            "card": 40,
            "channel": 3,
            "current": 1  
        }
    }

    response = txrx_command(redisFixt, command)
    assert response['status'] == 'error', "Expected error status in response for invalid card"
    
    # Disable the output
    command["command"] = "disableOutput"
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'error', "Expected error status in response"

def test_loadconfig_bad_args(redisFixt):
    """Test that a loadconfig command with bad arguments returns an error."""
    # Now load the config
    command = {
        "command": "loadConfig",
        "args": {"enableOutputs": 'False', 
                 "createNewConfig": 'FakeNews'}  # This should enable all outputs that were saved
    }
    response = txrx_command(redisFixt, command)
    assert response['status'] == 'error', "Expected error status in response for bad arguments in loadConfig"
