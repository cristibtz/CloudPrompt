#!/usr/bin/env python3
"""Test script for Redis session store"""

import sys
import os
sys.path.append('/home/cristibtz/CloudPrompt')

from cloudprompt.agent.agent import test_session_store, get_session_health, list_all_sessions

def main():
    print("🧪 Testing Redis Session Store")
    print("=" * 50)
    
    # Test session store functionality
    test_session_store("test-redis-session")
    
    print("\n📊 Session Health Check:")
    health = get_session_health()
    for key, value in health.items():
        print(f"  {key}: {value}")
    
    print("\n📋 Active Sessions:")
    sessions = list_all_sessions()
    if sessions:
        for session_id, tokens in sessions.items():
            print(f"  {session_id}: {list(tokens.keys())}")
    else:
        print("  No active sessions found")

if __name__ == "__main__":
    main()
