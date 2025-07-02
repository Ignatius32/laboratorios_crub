#!/usr/bin/env python3
"""
Test script to verify the sync button functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.integrations.keycloak_admin_client import keycloak_admin
from app.models.models import Usuario, db

def test_sync_functionality():
    """Test the sync functionality that's called from the web interface"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Testing Sync Button Functionality")
        print("=" * 50)
        
        # Show current users before sync
        print("\n1. Current users in local database BEFORE sync:")
        users_before = Usuario.query.all()
        print(f"   Total users: {len(users_before)}")
        for user in users_before:
            print(f"   - {user.idUsuario} ({user.email}) - Role: {user.rol}")
        
        # Test the sync function directly (same as called from web interface)
        print("\n2. Calling sync_users_to_local_db()...")
        try:
            sync_stats = keycloak_admin.sync_users_to_local_db()
            print(f"   ✅ Sync completed successfully!")
            print(f"   📊 Results: {sync_stats}")
        except Exception as e:
            print(f"   ❌ Sync failed: {str(e)}")
            return
        
        # Show current users after sync
        print("\n3. Current users in local database AFTER sync:")
        users_after = Usuario.query.all()
        print(f"   Total users: {len(users_after)}")
        for user in users_after:
            labs = ', '.join([lab.nombre for lab in user.laboratorios]) if user.laboratorios else 'No labs'
            print(f"   - {user.idUsuario} ({user.email}) - Role: {user.rol} - Labs: {labs}")
        
        # Check specifically for user 12345678
        print("\n4. Checking specifically for user 12345678:")
        target_user = Usuario.query.filter_by(idUsuario='12345678').first()
        if target_user:
            print(f"   ✅ Found user 12345678:")
            print(f"      - ID: {target_user.idUsuario}")
            print(f"      - Name: {target_user.nombre} {target_user.apellido}")
            print(f"      - Email: {target_user.email}")
            print(f"      - Role: {target_user.rol}")
            print(f"      - Labs: {[lab.nombre for lab in target_user.laboratorios]}")
        else:
            print("   ❌ User 12345678 NOT found in local database")
        
        # Check Keycloak laboratorista users
        print("\n5. Checking Keycloak for laboratorista users:")
        try:
            kc_users = keycloak_admin.get_laboratorista_users()
            print(f"   Found {len(kc_users)} laboratorista users in Keycloak:")
            for kc_user in kc_users:
                username = kc_user.get('username', kc_user.get('id'))
                email = kc_user.get('email')
                print(f"   - {username} ({email})")
                
                # Check if this user exists in local DB
                local_user = Usuario.query.filter(
                    (Usuario.idUsuario == username) | (Usuario.email == email)
                ).first()
                if local_user:
                    print(f"     ✅ Exists in local DB as: {local_user.idUsuario}")
                else:
                    print(f"     ❌ NOT in local DB")
        except Exception as e:
            print(f"   ❌ Error getting Keycloak users: {str(e)}")

if __name__ == "__main__":
    test_sync_functionality()
