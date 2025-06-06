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
            "card": 12,  # Valid Card Number
            "channel": 100  # Invalid channel number
        }
    }
    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)
    response = json.loads(message['data'].decode())
    assert response['status'] == 'error', "Expected error status in response for invalid card"

