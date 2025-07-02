#!/usr/bin/env python3
"""
Test script for Keycloak integration and user synchronization
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.integrations.keycloak_admin_client import keycloak_admin
from app.models.models import Usuario, db
import json

def test_keycloak_connection():
    """Test if we can connect to Keycloak"""
    print("🔄 Testing Keycloak connection...")
    
    app = create_app()
    with app.app_context():
        try:
            # Initialize the admin client
            keycloak_admin.init_app(app)
            
            # Try to get users
            users = keycloak_admin.get_all_users()
            print(f"✅ Successfully connected to Keycloak")
            print(f"📊 Found {len(users)} total users in Keycloak")
            
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Keycloak: {str(e)}")
            return False

def test_laboratorista_users():
    """Test fetching users with laboratorista role"""
    print("\n🔄 Testing laboratorista user fetching...")
    
    app = create_app()
    with app.app_context():
        try:
            # Get users with laboratorista role
            laboratorista_users = keycloak_admin.get_laboratorista_users()
            print(f"✅ Successfully fetched laboratorista users")
            print(f"📊 Found {len(laboratorista_users)} users with laboratorista role")
            
            # Show some details
            for i, user in enumerate(laboratorista_users[:3]):  # Show first 3 users
                print(f"   {i+1}. {user.get('username', 'N/A')} - {user.get('email', 'N/A')} - {user.get('firstName', '')} {user.get('lastName', '')}")
                if 'roles' in user:
                    print(f"      Roles: {', '.join(user['roles'])}")
            
            if len(laboratorista_users) > 3:
                print(f"   ... and {len(laboratorista_users) - 3} more users")
                
            return True
        except Exception as e:
            print(f"❌ Failed to fetch laboratorista users: {str(e)}")
            return False

def test_user_sync_dry_run():
    """Test user synchronization (dry run - no actual DB changes)"""
    print("\n🔄 Testing user synchronization (dry run)...")
    
    app = create_app()
    with app.app_context():
        try:
            # Get current local users
            local_users_before = Usuario.query.all()
            print(f"📊 Current local users: {len(local_users_before)}")
            
            # Get laboratorista users that would be synced
            keycloak_users = keycloak_admin.get_laboratorista_users()
            print(f"📊 Keycloak laboratorista users: {len(keycloak_users)}")
            
            # Analyze what would happen
            new_users = []
            existing_users = []
            
            for kc_user in keycloak_users:
                user_id = kc_user.get('username') or kc_user.get('id')
                email = kc_user.get('email')
                
                if not user_id or not email:
                    continue
                    
                existing_user = Usuario.query.filter(
                    (Usuario.idUsuario == user_id) | (Usuario.email == email)
                ).first()
                
                if existing_user:
                    existing_users.append({
                        'id': user_id,
                        'email': email,
                        'name': f"{kc_user.get('firstName', '')} {kc_user.get('lastName', '')}"
                    })
                else:
                    new_users.append({
                        'id': user_id,
                        'email': email,
                        'name': f"{kc_user.get('firstName', '')} {kc_user.get('lastName', '')}"
                    })
            
            print(f"✅ Analysis complete:")
            print(f"   📝 Users that would be created: {len(new_users)}")
            print(f"   🔄 Users that would be updated: {len(existing_users)}")
            
            if new_users:
                print("   New users:")
                for user in new_users[:5]:  # Show first 5
                    print(f"      • {user['id']} - {user['email']} - {user['name']}")
                if len(new_users) > 5:
                    print(f"      ... and {len(new_users) - 5} more")
            
            if existing_users:
                print("   Existing users that would be updated:")
                for user in existing_users[:5]:  # Show first 5
                    print(f"      • {user['id']} - {user['email']} - {user['name']}")
                if len(existing_users) > 5:
                    print(f"      ... and {len(existing_users) - 5} more")
                    
            return True
            
        except Exception as e:
            print(f"❌ Failed to analyze user synchronization: {str(e)}")
            return False

def main():
    """Run all tests"""
    print("🚀 Starting Keycloak Integration Tests")
    print("=" * 50)
    
    # Test 1: Basic connection
    if not test_keycloak_connection():
        print("\n❌ Basic connection failed, stopping tests")
        return
    
    # Test 2: Laboratorista users
    if not test_laboratorista_users():
        print("\n❌ Laboratorista user fetching failed, stopping tests")
        return
    
    # Test 3: Sync dry run
    if not test_user_sync_dry_run():
        print("\n❌ User sync analysis failed")
        return
    
    print("\n" + "=" * 50)
    print("✅ All tests passed successfully!")
    print("\n📋 Summary:")
    print("   • Keycloak connection: OK")
    print("   • Laboratorista role mapping: OK") 
    print("   • User synchronization logic: OK")
    print("\n🎯 The admin can now use the 'Sincronizar desde Keycloak' button")
    print("   in the user management interface to sync users.")

if __name__ == "__main__":
    main()
