"""
Script para actualizar la configuración de Keycloak de v22 a v26
Actualiza automáticamente todas las referencias de URL en el proyecto
"""

import os
import re
import shutil
from pathlib import Path

# Configuration
OLD_URL_PATTERN = r'huayca\.crub\.uncoma\.edu\.ar/auth/?'
NEW_URL = 'huayca.crub.uncoma.edu.ar/keycloak/'
BACKUP_SUFFIX = '.bak_v22'

def find_files_with_keycloak_config(root_dir):
    """Find all files that might contain Keycloak configuration"""
    patterns = [
        '*.py',
        '*.html', 
        '*.js',
        '*.json',
        '*.md',
        '*.txt',
        '.env*',
        'config.*'
    ]
    
    files_to_check = []
    
    for pattern in patterns:
        files_to_check.extend(Path(root_dir).rglob(pattern))
    
    # Filter out some directories we don't want to modify
    exclude_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'logs'}
    
    filtered_files = []
    for file_path in files_to_check:
        if not any(exclude_dir in file_path.parts for exclude_dir in exclude_dirs):
            filtered_files.append(file_path)
    
    return filtered_files

def backup_file(file_path):
    """Create a backup of the file"""
    backup_path = str(file_path) + BACKUP_SUFFIX
    try:
        shutil.copy2(file_path, backup_path)
        print(f"  ✓ Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to backup {file_path}: {e}")
        return False

def update_file_content(file_path):
    """Update Keycloak URLs in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file contains old Keycloak URL
        if not re.search(OLD_URL_PATTERN, content):
            return False, "No Keycloak URLs found"
        
        # Create backup
        if not backup_file(file_path):
            return False, "Backup failed"
        
        # Perform replacements
        updated_content = content
        
        # Replace various patterns
        replacements = [
            # Basic URL replacement
            (r'huayca\.crub\.uncoma\.edu\.ar/auth/?', NEW_URL),
            # Quoted URLs
            (r'"huayca\.crub\.uncoma\.edu\.ar/auth/?', f'"{NEW_URL}'),
            (r"'huayca\.crub\.uncoma\.edu\.ar/auth/?", f"'{NEW_URL}"),
            # Environment variables
            (r'KEYCLOAK_SERVER_URL=.*huayca\.crub\.uncoma\.edu\.ar/auth/?', f'KEYCLOAK_SERVER_URL={NEW_URL}'),
            # Comments about v22
            (r'# ?Keycloak v22', '# Keycloak v26'),
            (r'# ?Old v22', '# Old v22 (deprecated)'),
        ]
        
        changes_made = 0
        for pattern, replacement in replacements:
            new_content, count = re.subn(pattern, replacement, updated_content, flags=re.IGNORECASE)
            if count > 0:
                updated_content = new_content
                changes_made += count
        
        if changes_made > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            return True, f"{changes_made} replacements made"
        else:
            return False, "No changes needed"
            
    except Exception as e:
        return False, f"Error: {e}"

def update_environment_file():
    """Update .env file with new Keycloak URL"""
    env_files = ['.env', '.env.local', '.env.production']
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"\n📝 Updating {env_file}...")
            
            try:
                with open(env_file, 'r') as f:
                    lines = f.readlines()
                
                # Backup
                backup_path = env_file + BACKUP_SUFFIX
                shutil.copy2(env_file, backup_path)
                print(f"  ✓ Backup created: {backup_path}")
                
                updated_lines = []
                changes_made = False
                
                for line in lines:
                    if 'KEYCLOAK_SERVER_URL' in line and '/auth' in line:
                        # Update the line
                        if '=' in line:
                            key, value = line.split('=', 1)
                            # Remove quotes and trailing slash, then add new URL
                            value = value.strip().strip('"\'').rstrip('/')
                            new_line = f"{key}={NEW_URL}\n"
                            updated_lines.append(new_line)
                            changes_made = True
                            print(f"  ✓ Updated: {line.strip()} -> {new_line.strip()}")
                        else:
                            updated_lines.append(line)
                    else:
                        updated_lines.append(line)
                
                if changes_made:
                    with open(env_file, 'w') as f:
                        f.writelines(updated_lines)
                    print(f"  ✅ {env_file} updated successfully")
                else:
                    print(f"  ℹ️  No Keycloak URLs found in {env_file}")
                    
            except Exception as e:
                print(f"  ✗ Error updating {env_file}: {e}")

def main():
    """Main function to update all Keycloak configuration"""
    print("🔄 Updating Keycloak configuration from v22 to v26")
    print("=" * 60)
    
    print(f"Old URL pattern: {OLD_URL_PATTERN}")
    print(f"New URL: {NEW_URL}")
    print()
    
    # Update environment files first
    update_environment_file()
    
    # Find all relevant files
    print("\n🔍 Scanning for files with Keycloak configuration...")
    files_to_check = find_files_with_keycloak_config('.')
    print(f"Found {len(files_to_check)} files to check")
    
    # Update each file
    updated_files = 0
    error_files = 0
    skipped_files = 0
    
    for file_path in files_to_check:
        print(f"\n📄 Checking: {file_path}")
        
        success, message = update_file_content(file_path)
        
        if success:
            print(f"  ✅ Updated: {message}")
            updated_files += 1
        elif "No Keycloak URLs found" in message:
            print(f"  ⏭️  Skipped: {message}")
            skipped_files += 1
        else:
            print(f"  ❌ Error: {message}")
            error_files += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"✅ Files updated: {updated_files}")
    print(f"⏭️  Files skipped: {skipped_files}")
    print(f"❌ Files with errors: {error_files}")
    print(f"📁 Total files checked: {len(files_to_check)}")
    
    if updated_files > 0:
        print(f"\n💾 Backup files created with suffix: {BACKUP_SUFFIX}")
        print("🔄 To rollback changes, rename .bak_v22 files back to original names")
    
    print("\n✅ Keycloak v26 migration completed!")
    print("\n📋 Next steps:")
    print("1. Update your .env file with the correct KEYCLOAK_SERVER_URL")
    print("2. Test the login functionality")
    print("3. Verify all Keycloak endpoints are working")
    print("4. Remove backup files when confident the migration is successful")

if __name__ == "__main__":
    main()
