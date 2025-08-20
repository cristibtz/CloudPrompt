#!/usr/bin/env python3

import sys
import os
from datetime import datetime, timedelta
import random

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.db import SessionLocal
from app.models.user import User
from app.models.prompts import Prompt

def create_dummy_data():
    """Create dummy users and prompts for testing."""
    
    db = SessionLocal()
    
    try:
        print("Creating dummy data...")
        
        # Create dummy users
        users_data = [
            {"username": "john_doe", "email": "john@example.com", "credits": 100},
            {"username": "jane_smith", "email": "jane@example.com", "credits": 250},
            {"username": "admin_user", "email": "admin@cloudprompt.com", "credits": 500},
            {"username": "developer", "email": "dev@example.com", "credits": 150},
            {"username": "tester", "email": "test@example.com", "credits": 75},
        ]
        
        users = []
        for user_data in users_data:
            user = User(**user_data)
            db.add(user)
            users.append(user)
        
        db.commit()
        print(f"✅ Created {len(users)} users")
        
        # Refresh users to get their IDs
        for user in users:
            db.refresh(user)
        
        # Create dummy prompts with various providers
        prompt_examples = [
            {
                "prompt": "List all EC2 instances in us-east-1",
                "response": '{"instances": [{"id": "i-1234567890abcdef0", "type": "t3.micro", "state": "running"}]}',
                "provider": "aws"
            },
            {
                "prompt": "Create a new S3 bucket called my-test-bucket",
                "response": '{"bucket": "my-test-bucket", "status": "created", "region": "us-east-1"}',
                "provider": "aws"
            },
            {
                "prompt": "Show me all VMs in my Proxmox cluster",
                "response": "I can assist with AWS-related queries, but I'm unable to interact with Proxmox nodes directly. Please configure your Proxmox credentials.",
                "provider": "proxmox"
            },
            {
                "prompt": "List all resource groups in Azure",
                "response": '{"resource_groups": [{"name": "production-rg", "location": "East US"}, {"name": "development-rg", "location": "West US"}]}',
                "provider": "azure"
            },
            {
                "prompt": "Create a new VM with 2 CPUs and 4GB RAM",
                "response": '{"vm_id": "vm-456", "status": "creating", "specs": {"cpu": 2, "memory": "4GB"}}',
                "provider": "gcp"
            },
            {
                "prompt": "Stop all running instances",
                "response": '{"stopped_instances": ["i-1234567890abcdef0", "i-0987654321fedcba0"], "count": 2}',
                "provider": "aws"
            },
            {
                "prompt": "Get billing information for this month",
                "response": '{"current_month_cost": "$45.67", "projected_month_cost": "$52.30", "top_services": ["EC2", "S3", "RDS"]}',
                "provider": "aws"
            },
            {
                "prompt": "Create a load balancer for my web application",
                "response": '{"load_balancer": {"name": "web-app-lb", "dns": "web-app-lb-123456789.us-east-1.elb.amazonaws.com", "status": "provisioning"}}',
                "provider": "aws"
            },
            {
                "prompt": "List all storage accounts in Azure",
                "response": '{"storage_accounts": [{"name": "prodstg001", "type": "Standard_LRS"}, {"name": "devstg001", "type": "Standard_GRS"}]}',
                "provider": "azure"
            },
            {
                "prompt": "Show me my GCP project quotas",
                "response": '{"quotas": {"compute_instances": {"used": 5, "limit": 24}, "persistent_disks": {"used": "2TB", "limit": "10TB"}}}',
                "provider": "gcp"
            },
            {
                "prompt": "Start my development environment",
                "response": "Unable to connect to Proxmox API. Please check your network connectivity and credentials.",
                "provider": "proxmox"
            },
            {
                "prompt": "Create a new RDS MySQL instance",
                "response": '{"db_instance": {"identifier": "myapp-db", "engine": "mysql", "status": "creating", "endpoint": "pending"}}',
                "provider": "aws"
            }
        ]
        
        prompts = []
        for i, prompt_data in enumerate(prompt_examples):
            # Assign prompts to random users
            user = random.choice(users)
            
            # Create prompts with different timestamps (last 30 days)
            created_at = datetime.utcnow() - timedelta(days=random.randint(0, 30), 
                                                     hours=random.randint(0, 23), 
                                                     minutes=random.randint(0, 59))
            
            prompt = Prompt(
                user_id=user.id,
                prompt=prompt_data["prompt"],
                response=prompt_data["response"],
                provider=prompt_data["provider"],
                created_at=created_at
            )
            db.add(prompt)
            prompts.append(prompt)
        
        db.commit()
        print(f"✅ Created {len(prompts)} prompts")
        
        # Print summary
        print("\n📊 Database Summary:")
        print(f"   Users: {len(users)}")
        print(f"   Prompts: {len(prompts)}")
        print(f"   Providers used: {len(set(p['provider'] for p in prompt_examples))}")
        
        print("\n👤 Created Users:")
        for user in users:
            db.refresh(user)
            print(f"   • {user.username} ({user.email}) - {user.credits} credits - {len(user.prompts)} prompts")
        
        print("\n🔥 Recent Prompts:")
        recent_prompts = sorted(prompts, key=lambda p: p.created_at, reverse=True)[:5]
        for prompt in recent_prompts:
            print(f"   • [{prompt.provider}] {prompt.prompt[:50]}...")
        
        print("\n✅ Dummy data created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating dummy data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_dummy_data()
