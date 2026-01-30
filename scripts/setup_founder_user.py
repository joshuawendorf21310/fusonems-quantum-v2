#!/usr/bin/env python3
"""
Setup script to create or update the founder user account.
This script creates/updates a user with founder role and the specified credentials.
"""

import sys
import os

# Add backend to path - handle both direct execution and Docker execution
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_dir = os.path.join(project_root, 'backend')
backend_dir = os.path.abspath(backend_dir)

# Check if we're in Docker (backend dir exists) or running locally
if os.path.exists(backend_dir):
    sys.path.insert(0, backend_dir)
    # In Docker, we're at /app, so backend is at /app/backend
    # But imports expect to be run from /app, so add /app to path
    if os.path.exists('/app'):
        sys.path.insert(0, '/app')
        os.chdir('/app')
    else:
        os.chdir(backend_dir)
else:
    # Running locally, add backend to path
    sys.path.insert(0, backend_dir)

from sqlalchemy.orm import Session
from core.database import SessionLocal
# Use direct bcrypt to avoid passlib issues
import bcrypt
def hash_password(password: str) -> str:
    """Hash password using bcrypt directly."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
from models.user import User, UserRole
from models.organization import Organization
from models.module_registry import ModuleRegistry
from core.config import settings

# Founder credentials
FOUNDER_EMAIL = "joshua.j.wendorf@fusionemsquantum.com"
FOUNDER_PASSWORD = "Addyson21310#"
FOUNDER_NAME = "Joshua Wendorf"
ORG_NAME = "Fusion EMS Quantum"


def setup_founder_user():
    """Create or update the founder user account."""
    # Create tables if they don't exist
    try:
        from core.database import Base, get_engine
        from models.organization import Organization
        from models.user import User
        # Only create Organization and User tables for this script
        Base.metadata.create_all(get_engine(), tables=[Organization.__table__, User.__table__])
        print("✓ Database tables verified/created")
    except Exception as e:
        print(f"⚠ Warning: Could not create tables: {e}")
        print("  Continuing anyway - tables may already exist or migrations needed")
    
    db: Session = SessionLocal()
    
    try:
        # Get or create organization
        org = db.query(Organization).filter(Organization.name == ORG_NAME).first()
        if not org:
            print(f"Creating organization: {ORG_NAME}")
            org = Organization(name=ORG_NAME)
            db.add(org)
            db.commit()
            db.refresh(org)
            print(f"✓ Organization created with ID: {org.id}")
        else:
            print(f"✓ Using existing organization: {org.name} (ID: {org.id})")
        
        # Check if user exists
        user = db.query(User).filter(User.email == FOUNDER_EMAIL).first()
        
        if user:
            print(f"Found existing user: {FOUNDER_EMAIL}")
            # Update user to ensure founder role and correct password
            updated = False
            if user.role != UserRole.founder.value:
                print(f"  Updating role from '{user.role}' to 'founder'")
                user.role = UserRole.founder.value
                updated = True
            if user.full_name != FOUNDER_NAME:
                print(f"  Updating full_name to '{FOUNDER_NAME}'")
                user.full_name = FOUNDER_NAME
                updated = True
            if user.org_id != org.id:
                print(f"  Updating org_id to {org.id}")
                user.org_id = org.id
                updated = True
            
            # Always update password to ensure it's correct
            print(f"  Updating password...")
            user.hashed_password = hash_password(FOUNDER_PASSWORD)
            updated = True
            
            # Remove must_change_password flag if set
            if hasattr(user, 'must_change_password') and user.must_change_password:
                print(f"  Removing must_change_password flag")
                user.must_change_password = False
                updated = True
            
            if updated:
                db.commit()
                db.refresh(user)
                print(f"✓ User updated successfully")
            else:
                print(f"✓ User already configured correctly")
        else:
            print(f"Creating new founder user: {FOUNDER_EMAIL}")
            user = User(
                email=FOUNDER_EMAIL,
                full_name=FOUNDER_NAME,
                hashed_password=hash_password(FOUNDER_PASSWORD),
                role=UserRole.founder.value,
                org_id=org.id,
            )
            # Set must_change_password to False if the attribute exists
            if hasattr(User, 'must_change_password'):
                user.must_change_password = False
            
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✓ Founder user created successfully (ID: {user.id})")
        
        print("\n" + "="*60)
        print("Founder Account Setup Complete")
        print("="*60)
        print(f"Email:    {FOUNDER_EMAIL}")
        print(f"Password: {FOUNDER_PASSWORD}")
        print(f"Role:     {user.role}")
        print(f"Org ID:   {user.org_id}")
        print("="*60)
        print("\nYou can now log in with these credentials at /login")
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error setting up founder user: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print("Setting up founder user account...")
    print(f"Email: {FOUNDER_EMAIL}")
    print(f"Organization: {ORG_NAME}\n")
    setup_founder_user()
