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
        time.sleep(5) # Wait for bias crate daemon to start assuming it was ran from ./test in sparkbiasd
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
    redis_client.publish('sparkommand', json.dumps(command))
    
    print(pubsub.get_message())
    message = pubsub.get_message(ignore_subscribe_messages=True, timeout=5.0)
    pubsub.unsubscribe('sparkreply')
    assert message is not None, "No response received from Redis"
    
    response = json.loads(message['data'].decode())
    print(f"Response: {response}")
    assert response['status'] == 'success', "Expected success status in response"
    assert response['card'] == 1, "Expected card 1 in response"
    assert response['channel'] == 1, "Expected channel 1 in response"

def test_command_Nonsense(redis_client):
    command = "Aperture Science, we do what we must because we can"
    

def test_command_bad_command(redis_client):
    """Test that an erroneous command returns an error."""
    command = {
        "command": "Eat it scrub",
    }
    pubsub = redis_client.pubsub()
    pubsub.subscribe('sparkreply')
    redis_client.publish('sparkommand', json.dumps(command))
    # Wait for a response
    hrm = pubsub.get_message()
    assert hrm['type'] == "subscribe"
    message = pubsub.get_message(ignore_subscribe_messages=True, timeout=5.0)
    pubsub.unsubscribe('sparkreply')

    assert message is not None, "No response received from Redis"
    response = json.loads(message['data'].decode())
    assert response['status'] == 'error', "Expected error status in response"