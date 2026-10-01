#!/usr/bin/env python3
"""
Debug script for Keycloak user synchronization
Run this to test the Keycloak integration and see what users and roles are found
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.integrations.keycloak_admin_client import keycloak_admin

def test_keycloak_sync():
    """Test Keycloak synchronization process for laboratorios-crub-dev client"""
    app = create_app()
    
    with app.app_context():
        print("🔍 Testing Keycloak Integration for laboratorios-crub-dev client")
        print("=" * 60)
        
        try:
            # Test connection
            print("1. Testing Keycloak connection...")
            if keycloak_admin.admin_client is None:
                print("❌ Failed to connect to Keycloak")
                return
            print("✅ Connected to Keycloak successfully")
            
            # Get client information
            print("\n2. Getting client information...")
            
            # Show current configuration
            print(f"📝 Current configuration:")
            print(f"   KEYCLOAK_SERVER_URL: {app.config.get('KEYCLOAK_SERVER_URL', 'Not set')}")
            print(f"   KEYCLOAK_REALM: {app.config.get('KEYCLOAK_REALM', 'Not set')}")
            print(f"   KEYCLOAK_CLIENT_ID: {app.config.get('KEYCLOAK_CLIENT_ID', 'Not set')}")
            print(f"   KEYCLOAK_ADMIN_ROLE: {app.config.get('KEYCLOAK_ADMIN_ROLE', 'Not set')}")
            print(f"   KEYCLOAK_TECNICO_ROLE: {app.config.get('KEYCLOAK_TECNICO_ROLE', 'Not set')}")
            
            # Use the configured client ID
            target_client_id = app.config.get('KEYCLOAK_CLIENT_ID', 'laboratorios-crub-dev')
            print(f"🎯 Target client: {target_client_id}")
            
            if not target_client_id:
                print("❌ No client ID configured!")
                return
            
            try:
                client_uuid = keycloak_admin.admin_client.get_client_id(target_client_id)
                print(f"✅ Found client UUID: {client_uuid}")
                
                if client_uuid is None:
                    print(f"❌ Client '{target_client_id}' returned None UUID")
                    
                    # Let's try to list all available clients
                    print("\n🔍 Listing all available clients:")
                    try:
                        all_clients = keycloak_admin.admin_client.get_clients()
                        print(f"   Found {len(all_clients)} clients in realm")
                        for client in all_clients[:15]:  # Show first 15 clients
                            client_id = client.get('clientId', 'N/A')
                            client_name = client.get('name', 'N/A')
                            print(f"   - {client_id} (Name: {client_name}, ID: {client.get('id')})")
                    except Exception as list_error:
                        print(f"   ❌ Could not list clients: {list_error}")
                    return
                    
            except Exception as e:
                print(f"❌ Failed to find client '{target_client_id}': {e}")
                
                # Let's try to list all available clients
                print("\n🔍 Listing all available clients:")
                try:
                    all_clients = keycloak_admin.admin_client.get_clients()
                    print(f"   Found {len(all_clients)} clients in realm")
                    for client in all_clients[:15]:  # Show first 15 clients
                        client_id = client.get('clientId', 'N/A')
                        client_name = client.get('name', 'N/A')
                        print(f"   - {client_id} (Name: {client_name}, ID: {client.get('id')})")
                except Exception as list_error:
                    print(f"   ❌ Could not list clients: {list_error}")
                return
            
            # Get client roles
            print(f"\n3. Getting roles from client '{target_client_id}'...")
            try:
                client_roles = keycloak_admin.admin_client.get_client_roles(client_uuid)
                print(f"📋 Found {len(client_roles)} client roles:")
                for role in client_roles:
                    print(f"   - {role['name']}")
            except Exception as e:
                print(f"❌ Failed to get client roles: {e}")
                return
            
            # Get all users
            print("\n4. Getting all users from Keycloak...")
            all_users = keycloak_admin.get_all_users()
            print(f"📊 Found {len(all_users)} total users in realm")
            
            # Test specific users and their client roles
            print(f"\n5. Testing specific users for client roles...")
            test_users = ['app_admin', 'laboratorita']
            admin_role = app.config.get('KEYCLOAK_ADMIN_ROLE', 'app_admin')
            laboratorista_role = app.config.get('KEYCLOAK_TECNICO_ROLE', 'laboratorista')
            
            print(f"🔍 Looking for admin role: '{admin_role}'")
            print(f"🔍 Looking for laboratorista role: '{laboratorista_role}'")
            
            found_users = []
            for username in test_users:
                print(f"\n👤 Searching for user: {username}")
                user = keycloak_admin.get_user_by_username(username)
                
                if user:
                    print(f"   ✅ Found user: {user.get('username')} ({user.get('email', 'N/A')})")
                    user_id = user['id']
                    
                    # Get client roles for this specific user
                    try:
                        client_roles_for_user = keycloak_admin.admin_client.get_client_roles_of_user(user_id, client_uuid)
                        realm_roles_for_user = keycloak_admin.admin_client.get_realm_roles_of_user(user_id)
                        
                        print(f"   � Client roles: {[role['name'] for role in client_roles_for_user] if client_roles_for_user else 'None'}")
                        print(f"   📋 Realm roles: {[role['name'] for role in realm_roles_for_user] if realm_roles_for_user else 'None'}")
                        
                        # Check for specific roles
                        client_role_names = [role['name'] for role in client_roles_for_user] if client_roles_for_user else []
                        
                        if admin_role in client_role_names:
                            print(f"   ✅ Has '{admin_role}' role in client!")
                        elif laboratorista_role in client_role_names:
                            print(f"   ✅ Has '{laboratorista_role}' role in client!")
                        else:
                            print(f"   ❌ Does not have expected roles in client")
                        
                        found_users.append({
                            'user': user,
                            'client_roles': client_role_names,
                            'realm_roles': [role['name'] for role in realm_roles_for_user] if realm_roles_for_user else []
                        })
                        
                    except Exception as e:
                        print(f"   ❌ Failed to get roles for user: {e}")
                else:
                    print(f"   ❌ User not found")
            
            print(f"\n6. Summary of client-specific users:")
            print(f"   Users found: {len(found_users)}")
            for user_data in found_users:
                user = user_data['user']
                print(f"   - {user.get('username')} ({user.get('email', 'N/A')})")
                print(f"     Client roles: {user_data['client_roles']}")
                print(f"     Realm roles: {user_data['realm_roles']}")
            
            # Test getting users by client role
            print(f"\n7. Testing client role-based user retrieval...")
            for role_name in [admin_role, laboratorista_role]:
                print(f"\n   Testing role: {role_name}")
                users_with_role = get_client_users_by_role(keycloak_admin.admin_client, client_uuid, role_name)
                print(f"   Found {len(users_with_role)} users with role '{role_name}'")
            
                for user_info in users_with_role:
                    print(f"     - {user_info['username']} ({user_info.get('email', 'N/A')})")
            
            # Test the actual sync process
            print(f"\n8. Testing actual sync process...")
            print("   Note: This will show what users would be synced (dry run)")
            
            # Import the sync function to test it
            sync_stats = keycloak_admin.sync_users_to_local_db()
            print(f"   Sync results: {sync_stats}")
            
            # Show current local users with laboratorios assignment
            print(f"\n9. Current local users and their laboratory assignments:")
            from app.models.models import Usuario
            local_users = Usuario.query.filter_by(rol='tecnico').all()
            print(f"   Found {len(local_users)} local technical users:")
            for user in local_users:
                labs = [lab.nombre for lab in user.laboratorios]
                print(f"     - {user.idUsuario} ({user.email}) - Labs: {labs if labs else 'No labs assigned'}")
            
            print("\n✅ Complete debugging finished!")
            
        except Exception as e:
            print(f"\n❌ Error during debugging: {str(e)}")
            import traceback
            traceback.print_exc()

def get_client_users_by_role(admin_client, client_uuid, role_name):
    """Get all users that have a specific client role"""
    try:
        users_with_role = []
        
        # Get the role object
        role = admin_client.get_client_role(client_uuid, role_name)
        if not role:
            return users_with_role
        
        # Get all users
        all_users = admin_client.get_users()
        
        for user in all_users:
            user_id = user['id']
            try:
                # Get client roles for this user
                client_roles = admin_client.get_client_roles_of_user(user_id, client_uuid)
                client_role_names = [r['name'] for r in client_roles] if client_roles else []
                
                if role_name in client_role_names:
                    users_with_role.append(user)
            except Exception as e:
                print(f"     Warning: Could not get roles for user {user.get('username', user_id)}: {e}")
                continue
        
        return users_with_role
        
    except Exception as e:
        print(f"Error getting users by client role: {e}")
        return []

if __name__ == "__main__":
    test_keycloak_sync()
