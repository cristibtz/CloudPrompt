#!/usr/bin/env python3
"""Simple test for token extraction patterns."""

import re
import json

def extract_tokens_from_dict(data: dict) -> dict[str, str]:
    """Extract tokens from a dictionary response."""
    found = {}
    
    # Direct key lookup
    token_keys = {
        'environment_token',
        'credentials_token', 
        'generated_code_token',
        'explained_token',
        'execution_token',
        'security_scan_token',
        'request_token',
    }
    
    for key in token_keys:
        if key in data and isinstance(data[key], str):
            # Map execution_token to explained_token for consistency
            token_key = 'explained_token' if key == 'execution_token' else key
            found[token_key] = data[key]
    
    return found

def extract_tokens_from_text(text: str) -> dict[str, str]:
    """Extract tokens from text using regex patterns."""
    found = {}
    
    patterns = {
        'environment_token': r'\b(env_[a-f0-9\-]{30,})\b',
        'credentials_token': r'\b(creds_[a-f0-9\-]{30,})\b', 
        'generated_code_token': r'\b(generated_code_[a-f0-9\-]{30,})\b',
        'explained_token': r'\b(explained_[a-f0-9\-]{30,})\b',
        'security_scan_token': r'\b(sec_[a-f0-9\-]{30,})\b',
        'request_token': r'\b(req_[a-f0-9\-]{30,})\b',
    }
    
    for name, pattern in patterns.items():
        match = re.search(pattern, text)
        if match and name not in found:
            found[name] = match.group(1)
    
    return found

# Test data
test_response = {
    "credentials_token": "creds_396d27a0-abba-481d-b8fc-effb3eae121e",
    "message": "AWS session validated. Use this token with generate_infrastructure_code().",
    "account_id": "717279719563",
    "region": "us-east-1",
}

def main():
    print("Testing token extraction...")
    
    # Test direct dictionary extraction
    print("1. Testing direct dictionary extraction:")
    tokens = extract_tokens_from_dict(test_response)
    print(f"   Found tokens: {tokens}")
    
    # Test text extraction  
    print("2. Testing text extraction:")
    json_text = json.dumps(test_response)
    tokens_from_text = extract_tokens_from_text(json_text)
    print(f"   Found tokens: {tokens_from_text}")
    
    # Test with manual string
    print("3. Testing manual token string:")
    test_string = "Your credentials_token is creds_396d27a0-abba-481d-b8fc-effb3eae121e for use with other tools."
    tokens_manual = extract_tokens_from_text(test_string)
    print(f"   Found tokens: {tokens_manual}")
    
    return tokens

if __name__ == "__main__":
    main()
