#!/usr/bin/env python3
"""
Test script to verify automatic credential refresh functionality
"""
import asyncio
import json
from cloudprompt.agent.agent import run_aws_agent
from cloudprompt.agent.redis_session_store import RedisSessionStore

async def test_auto_refresh():
    """Test the auto-refresh functionality"""
    print("Testing auto-refresh functionality...")
    
    # Test with a user that has no session
    test_user = "test-auto-refresh-user"
    
    # First request - should work normally
    print("\n1. First request (should work normally):")
    result1 = await run_aws_agent("List my S3 buckets", {}, keycloak_id=test_user)
    
    if isinstance(result1, dict) and result1.get("auto_refresh"):
        print("✅ Auto-refresh response detected for new user (expected)")
        print(f"   Message: {result1.get('message')}")
        print(f"   Error: {result1.get('error')}")
    elif hasattr(result1, 'output'):
        print("✅ Normal response with output")
        print(f"   Output length: {len(result1.output)} characters")
    else:
        print("❌ Unexpected response format")
        print(f"   Result: {result1}")
    
    # Simulate invalid token by manually corrupting session data
    print("\n2. Simulating invalid token scenario:")
    session_store = RedisSessionStore()
    session_data = session_store.load(test_user)
    
    if session_data:
        # Corrupt the credentials token to simulate expiration
        if 'credentials_token' in session_data:
            session_data['credentials_token'] = 'invalid_token_123'
            session_store.save(test_user, session_data)
            print("   Corrupted credentials_token to simulate expiration")
        
        # Try another request with corrupted token
        result2 = await run_aws_agent("List my EC2 instances", {}, keycloak_id=test_user)
        
        if isinstance(result2, dict) and result2.get("auto_refresh"):
            print("✅ Auto-refresh response detected for corrupted token (expected)")
            print(f"   Message: {result2.get('message')}")
        elif hasattr(result2, 'output'):
            print("✅ Request succeeded despite corrupted token")
            print(f"   Output length: {len(result2.output)} characters")
        else:
            print("❌ Unexpected response format")
            print(f"   Result: {result2}")
    else:
        print("   No session data found, cannot test token corruption")
    
    # Clean up test session
    session_store.clear(test_user)
    print("\n3. Cleaned up test session")

if __name__ == "__main__":
    asyncio.run(test_auto_refresh())
