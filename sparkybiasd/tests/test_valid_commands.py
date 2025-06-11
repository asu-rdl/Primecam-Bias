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


def test_redis_connection(redisFixt):
    """Test if the Redis client can connect successfully."""
    redis_client, pubsub = redisFixt
    try:
        redis_client.ping()
    except redis.exceptions.ConnectionError:
        pytest.fail("Redis connection failed")

    
def test_command_get_status(redisFixt):
    """Test the get_status command."""
    redis_client, pubsub = redisFixt
    # Simulate a command to get status for card 1, channel 1
    command = {
        "command": "getStatus",
        "args": {
            "card": 1,
            "channel": 1
        }
    }


    redis_client.publish('sparkommand', json.dumps(command))

    message = pubsub.get_message(True, timeout=None)

    
    response = json.loads(message['data'].decode())
    print(f"Response: {response}")
    assert response['status'] == 'success', "Expected success status in response"
    assert response['card'] == 1, "Expected card 1 in response"
    assert response['channel'] == 1, "Expected channel 1 in response"

def test_enable_output(redisFixt):
    """Test that we set an output."""
    redis_client, pubsub = redisFixt
    command = {
        "command": "enableOutput",
        "args": {
            "card": 1,
            "channel": 1,
        }
    }
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'success', "Expected success status in response"

def test_command_seek_voltage(redisFixt):
    """Test that we can seek a voltage."""
    redis_client, pubsub = redisFixt
    command = {
        "command": "enableOutput",
        "args": {
            "card": 1,
            "channel": 1,
        }
    }
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
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

    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'success', "Expected success status in response"
    assert response['card'] == 1, "Expected card 1 in response"
    assert response['channel'] == 1, "Expected channel 1 in response"

def test_command_disable_output(redisFixt):
    """Test that we can disable an output."""
    redis_client, pubsub = redisFixt
    command = {
        "command": "disableOutput",
        "args": {
            "card": 1,
            "channel": 1,
        }
    }
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'success', "Expected success status in response"

def test_command_enable_testload(redisFixt):
    """Test that we can enable a testload."""
    redis_client, pubsub = redisFixt
    command = {
        "command": "enableTestload",
        "args": {
            "card": 10,
            "channel": 5,
        }
    }
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'success', "Expected success status in response"

def test_command_disable_testload(redisFixt):
    """Test that we can enable a testload."""
    redis_client, pubsub = redisFixt
    command = {
        "command": "disableTestload",
        "args": {
            "card": 10,
            "channel": 5,
        }
    }
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'success', "Expected success status in response"

def test_command_test_set_channel(redisFixt):
    """
    This is not an automated test, but a manual one.
    A channel is enabled, then a testload is enabled,
    then the channel is set to a voltage, and then the testload
    is disabled. The channel should be at 0V after this. The voltage change should be ovservable
    in the application logs.
    """
    redis_client, pubsub = redisFixt
    command = {
        "command": "enableOutput",
        "args": {
            "card": 1,
            "channel": 1,
        }
    }
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'success', "Expected success status in response"

    command["command"] = "enableTestload"
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'success', "Expected success status in response"

    command["command"] = "seekVoltage"
    command["args"]["voltage"] = 2.0
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'success', "Expected success status in response"

    command["command"] = "disableTestload"
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'success', "Expected success status in response"

    command["command"] = "disableOutput"
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'success', "Expected success status in response"


def test_command_seek_current(redisFixt):
    """Test that we can seek a voltage."""

    # Enable the output first
    redis_client, pubsub = redisFixt
    command = {
        "command": "enableOutput",
        "args": {
            "card": 10,
            "channel": 3,
        }
    }
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'success', "Expected success status in response"

    # Enable the testload
    command = {
        "command": "enableTestload",
        "args": {
            "card": 10,
            "channel": 3,
        }
    }
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
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

    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'success', "Expected success status in response"
    assert response['card'] == 10, "Expected card 1 in response"
    assert response['channel'] == 3, "Expected channel 1 in response"
    assert round(response['current']) == 10, "Expected current 10mA in response"
    
    # Disable the testload and output
    command["command"] = "disableTestload"
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'success', "Expected success status in response"
    command["command"] = "disableOutput"
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'success', "Expected success status in response"



def test_command_get_cards(redisFixt):
    """Test that we can get the list of cards connected to the bias crate."""
    redis_client, pubsub = redisFixt
    command = {
        "command": "getAvailableCards",
        "args": {}
    }
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'success', "Expected success status in response"