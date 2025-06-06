import pytest
import redis
import json
import os
import redis.exceptions
import time


@pytest.fixture
def redis_client():
    """Fixture to create a Redis client."""
    client = redis.Redis(host='10.206.160.58', port=6379)
    yield client
    client.close()

def test_redis_connection(redis_client):
    """Test if the Redis client can connect successfully."""
    try:
        time.sleep(4) # Wait for bias crate daemon to start assuming it was ran from ./test in sparkbiasd
        redis_client.ping()
    except redis.exceptions.ConnectionError:
        pytest.fail("Redis connection failed")

    
def test_command_get_status(redis_client):
    """Test the get_status command."""
    # Simulate a command to get status for card 1, channel 1
    command = {
        "command": "getStatus",
        "args": {
            "card": 1,
            "channel": 1
        }
    }
    pubsub = redis_client.pubsub()
    pubsub.subscribe('sparkreply')
    print(pubsub.get_message())

    redis_client.publish('sparkommand', json.dumps(command))
    time.sleep(1)

    message = pubsub.get_message(True, timeout=None)
    pubsub.unsubscribe('sparkreply')
    pubsub.get_message()  # Clear any remaining messages
    assert message is not None, "No response received from Redis"
    
    response = json.loads(message['data'].decode())
    print(f"Response: {response}")
    assert response['status'] == 'success', "Expected success status in response"
    assert response['card'] == 1, "Expected card 1 in response"
    assert response['channel'] == 1, "Expected channel 1 in response"

def test_command_Nonsense(redis_client):
    command = "Aperture Science, we do what we must because we \ncan for the good of all of us. Except the ones who are dead."
    pubsub = redis_client.pubsub()
    pubsub.subscribe('sparkreply')
    pubsub.get_message()

    redis_client.publish('sparkommand', json.dumps(command))
    message = pubsub.get_message(True, timeout=None)

    pubsub.unsubscribe('sparkreply')
    pubsub.get_message()  # Clear any remaining messages
    assert message is not None, "No response received from Redis"
    response = json.loads(message['data'].decode())
    assert response['status'] == 'error', "Expected error status in response"

def test_command_bad_command(redis_client):
    """Test that an erroneous command returns an error."""
    command = {
        "command": "FailHardFailOften",
    }
    pubsub = redis_client.pubsub()
    pubsub.subscribe('sparkreply')
    redis_client.publish('sparkommand', json.dumps(command))
    # Wait for a response
    hrm = pubsub.get_message()
    assert hrm['type'] == "subscribe"
    message = pubsub.get_message(True, timeout=None)
    pubsub.unsubscribe('sparkreply')
    pubsub.get_message()  # Clear any remaining messages
    assert message is not None, "No response received from Redis"
    response = json.loads(message['data'].decode())
    assert response['status'] == 'error', "Expected error status in response"
    time.sleep(0.1)


def test_command_get_status_badargs(redis_client):
    """Test the get_status command."""
    pubsub = redis_client.pubsub()
    pubsub.subscribe('sparkreply')
    pubsub.get_message()
    def dothing(myCommand):

        redis_client.publish('sparkommand', json.dumps(myCommand))
        time.sleep(2)

        message = pubsub.get_message(True, timeout=None)
        assert message is not None, "No response received from Redis"
        return json.loads(message['data'].decode())
    
    command = {
        "command": "getStatus",
        "args": {
            "card": 100,  # Invalid card number
            "channel": 1
        }
    }
    command_two = {
        "command": "getStatus",
        "args": {
            "card": 6,  # Valid Card Number
            "channel": 100  # Invalid channel number
        }
    }
    command_three = {
        "command": "getStatus",
    }
    command_four = {
        "command": "getStatus",
        "args": {}
    }
    response = dothing(command)
    assert response['status'] == 'error', "Expected error status in response for invalid card"
    assert response['code'] == -6, "Expected error code -6 for invalid card"

    response = dothing(command_two)
    assert response['status'] == 'error', "Expected error status in response for invalid channel"
    assert response['code'] == -7, "Expected error code -7 for invalid channel"

    response = dothing(command_three)
    assert response['status'] == 'error', "Expected error status in response for missing args"

    response = dothing(command_four)
    assert response['status'] == 'error', "Expected error status in response for empty args"