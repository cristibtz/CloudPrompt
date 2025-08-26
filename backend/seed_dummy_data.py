#!/usr/bin/env python3
"""
Seed script to populate the database with dummy data.
Run this script to add 5 users, 5 prompts, and 5 credentials to the database.
"""

import sys
import os
import base64
import json
from datetime import datetime, timedelta

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.db import SessionLocal
from app.models.user import User
from app.models.prompts import Prompt
from app.models.credentials import Credential

def create_dummy_credentials_data():
    """Create base64 encoded JSON credentials for AWS and Proxmox"""
    
    # AWS credentials structure
    aws_creds = {
        "access_key_id": "AKIA123456789EXAMPLE",
        "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    }
    
    # Proxmox credentials structure
    proxmox_creds = {
        "host": "proxmox.example.com",
        "username": "root@pam",
        "password": "proxmox_password_123",
    }
    
    # Encode to base64
    aws_encoded = base64.b64encode(json.dumps(aws_creds).encode()).decode()
    proxmox_encoded = base64.b64encode(json.dumps(proxmox_creds).encode()).decode()
    
    return aws_encoded, proxmox_encoded

def seed_database():
    """Seed the database with dummy data"""
    
    db = SessionLocal()
    
    try:
        # Clear existing data (optional - remove if you want to keep existing data)
        print("Clearing existing data...")
        db.query(Credential).delete()
        db.query(Prompt).delete()
        db.query(User).delete()
        db.commit()
        
        print("Creating dummy users...")
        
        # Create 5 users
        users = [
            User(
                keycloak_id="user-001-keycloak-id",
                username="alice_smith",
                email="alice@example.com",
                credits=100
            ),
            User(
                keycloak_id="user-002-keycloak-id",
                username="bob_jones",
                email="bob@example.com",
                credits=150
            ),
            User(
                keycloak_id="user-003-keycloak-id",
                username="charlie_brown",
                email="charlie@example.com",
                credits=75
            ),
            User(
                keycloak_id="user-004-keycloak-id",
                username="diana_wilson",
                email="diana@example.com",
                credits=200
            ),
            User(
                keycloak_id="user-005-keycloak-id",
                username="eve_garcia",
                email="eve@example.com",
                credits=125
            )
        ]
        
        # Add users to database
        for user in users:
            db.add(user)
        db.commit()
        
        # Refresh to get IDs
        for user in users:
            db.refresh(user)
        
        print(f"Created {len(users)} users")
        
        print("Creating dummy prompts...")
        
        # Create 5 prompts
        prompts = [
            Prompt(
                user_id=users[0].id,
                prompt="Create an EC2 instance with Ubuntu 22.04",
                response="EC2 instance i-1234567890abcdef0 created successfully",
                provider="aws",
                created_at=datetime.utcnow() - timedelta(days=5)
            ),
            Prompt(
                user_id=users[1].id,
                prompt="List all virtual machines in Proxmox",
                response="Found 3 VMs: vm-101, vm-102, vm-103",
                provider="proxmox",
                created_at=datetime.utcnow() - timedelta(days=4)
            ),
            Prompt(
                user_id=users[2].id,
                prompt="Create S3 bucket for backup storage",
                response="S3 bucket 'backup-storage-2024' created successfully",
                provider="aws",
                created_at=datetime.utcnow() - timedelta(days=3)
            ),
            Prompt(
                user_id=users[3].id,
                prompt="Start virtual machine vm-101",
                response="Virtual machine vm-101 started successfully",
                provider="proxmox",
                created_at=datetime.utcnow() - timedelta(days=2)
            ),
            Prompt(
                user_id=users[4].id,
                prompt="Check AWS account billing",
                response="Current month charges: $45.67",
                provider="aws",
                created_at=datetime.utcnow() - timedelta(days=1)
            )
        ]
        
        # Add prompts to database
        for prompt in prompts:
            db.add(prompt)
        db.commit()
        
        print(f"Created {len(prompts)} prompts")
        
        print("Creating dummy credentials...")
        
        # Get encoded credentials
        aws_encoded, proxmox_encoded = create_dummy_credentials_data()
        
        # Create 5 credentials (mix of AWS and Proxmox)
        credentials = [
            Credential(
                user_id=users[0].id,
                provider="aws",
                data=aws_encoded,
                created_at=datetime.utcnow() - timedelta(days=10)
            ),
            Credential(
                user_id=users[1].id,
                provider="proxmox",
                data=proxmox_encoded,
                created_at=datetime.utcnow() - timedelta(days=9)
            ),
            Credential(
                user_id=users[2].id,
                provider="aws",
                data=aws_encoded,
                created_at=datetime.utcnow() - timedelta(days=8)
            ),
            Credential(
                user_id=users[3].id,
                provider="proxmox",
                data=proxmox_encoded,
                created_at=datetime.utcnow() - timedelta(days=7)
            ),
            Credential(
                user_id=users[4].id,
                provider="aws",
                data=aws_encoded,
                created_at=datetime.utcnow() - timedelta(days=6)
            )
        ]
        
        # Add credentials to database
        for credential in credentials:
            db.add(credential)
        db.commit()
        
        print(f"Created {len(credentials)} credentials")
        
        # Show sample decoded credentials for verification
        print("\nSample credential data (decoded):")
        print("AWS credentials:")
        print(json.dumps(json.loads(base64.b64decode(aws_encoded).decode()), indent=2))
        print("\nProxmox credentials:")
        print(json.dumps(json.loads(base64.b64decode(proxmox_encoded).decode()), indent=2))
        
        print("\n" + "="*50)
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("="*50)
        print(f"✓ Users: {len(users)}")
        print(f"✓ Prompts: {len(prompts)}")
        print(f"✓ Credentials: {len(credentials)}")
        print("\nCredentials structure:")
        print("- AWS: access_key_id, secret_access_key")
        print("- Proxmox: host, username, password")
        print("\nAll credential data is base64 encoded JSON.")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting database seeding...")
    seed_database()
