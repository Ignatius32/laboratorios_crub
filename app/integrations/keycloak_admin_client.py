"""
Keycloak Admin Client for User Management
Handles administrative operations like user creation, role assignment, etc.
"""
from keycloak import KeycloakAdmin
from flask import current_app
import requests
from app.utils.logging_config import get_security_logger, get_audit_logger

class KeycloakAdminClient:
    """Keycloak Admin API client for user management"""
    
    def __init__(self, app=None):
        self.admin_client = None
        self.security_logger = get_security_logger()
        self.audit_logger = get_audit_logger()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        try:
            self.admin_client = KeycloakAdmin(
                server_url=app.config['KEYCLOAK_SERVER_URL'],
                realm_name=app.config['KEYCLOAK_REALM'],
                client_id=app.config['KEYCLOAK_CLIENT_ID'],
                client_secret_key=app.config['KEYCLOAK_CLIENT_SECRET'],
                verify=True
            )
            
            self.security_logger.info("Keycloak Admin client initialized",
                                    operation="admin_client_init",
                                    component="keycloak_admin",
                                    realm=app.config['KEYCLOAK_REALM'])
            
        except Exception as e:
            self.security_logger.error("Failed to initialize Keycloak Admin client",
                                     operation="admin_client_init",
                                     component="keycloak_admin",
                                     error=str(e))
            raise
    
    def create_user(self, user_data):
        """Create a new user in Keycloak"""
        try:
            user_id = self.admin_client.create_user(user_data)
            
            self.audit_logger.info("User created in Keycloak",
                                 operation="create_user",
                                 component="keycloak_admin",
                                 user_id=user_id,
                                 username=user_data.get('username'))
            
            return user_id
            
        except Exception as e:
            self.security_logger.error("Failed to create user in Keycloak",
                                     operation="create_user",
                                     component="keycloak_admin",
                                     username=user_data.get('username'),
                                     error=str(e))
            raise
    
    def get_user_by_username(self, username):
        """Get user by username"""
        try:
            users = self.admin_client.get_users({"username": username})
            if users:
                return users[0]
            return None
            
        except Exception as e:
            self.security_logger.error("Failed to get user by username",
                                     operation="get_user",
                                     component="keycloak_admin",
                                     username=username,
                                     error=str(e))
            return None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        try:
            users = self.admin_client.get_users({"email": email})
            if users:
                return users[0]
            return None
            
        except Exception as e:
            self.security_logger.error("Failed to get user by email",
                                     operation="get_user",
                                     component="keycloak_admin",
                                     email=email,
                                     error=str(e))
            return None
    
    def update_user(self, user_id, user_data):
        """Update user in Keycloak"""
        try:
            self.admin_client.update_user(user_id, user_data)
            
            self.audit_logger.info("User updated in Keycloak",
                                 operation="update_user",
                                 component="keycloak_admin",
                                 user_id=user_id)
            
            return True
            
        except Exception as e:
            self.security_logger.error("Failed to update user in Keycloak",
                                     operation="update_user",
                                     component="keycloak_admin",
                                     user_id=user_id,
                                     error=str(e))
            return False
    
    def delete_user(self, user_id):
        """Delete user from Keycloak"""
        try:
            self.admin_client.delete_user(user_id)
            
            self.audit_logger.info("User deleted from Keycloak",
                                 operation="delete_user",
                                 component="keycloak_admin",
                                 user_id=user_id)
            
            return True
            
        except Exception as e:
            self.security_logger.error("Failed to delete user from Keycloak",
                                     operation="delete_user",
                                     component="keycloak_admin",
                                     user_id=user_id,
                                     error=str(e))
            return False
    
    def assign_client_role(self, user_id, role_name):
        """Assign client role to user"""
        try:
            client_id = current_app.config['KEYCLOAK_CLIENT_ID']
            
            # Get client
            client = self.admin_client.get_client_id(client_id)
            
            # Get role
            role = self.admin_client.get_client_role(client, role_name)
            
            # Assign role
            self.admin_client.assign_client_role(user_id, client, role)
            
            self.audit_logger.info("Client role assigned to user",
                                 operation="assign_role",
                                 component="keycloak_admin",
                                 user_id=user_id,
                                 role_name=role_name)
            
            return True
            
        except Exception as e:
            self.security_logger.error("Failed to assign client role",
                                     operation="assign_role",
                                     component="keycloak_admin",
                                     user_id=user_id,
                                     role_name=role_name,
                                     error=str(e))
            return False
    
    def remove_client_role(self, user_id, role_name):
        """Remove client role from user"""
        try:
            client_id = current_app.config['KEYCLOAK_CLIENT_ID']
            
            # Get client
            client = self.admin_client.get_client_id(client_id)
            
            # Get role
            role = self.admin_client.get_client_role(client, role_name)
            
            # Remove role
            self.admin_client.delete_client_role_from_user(user_id, client, role)
            
            self.audit_logger.info("Client role removed from user",
                                 operation="remove_role",
                                 component="keycloak_admin",
                                 user_id=user_id,
                                 role_name=role_name)
            
            return True
            
        except Exception as e:
            self.security_logger.error("Failed to remove client role",
                                     operation="remove_role",
                                     component="keycloak_admin",
                                     user_id=user_id,
                                     role_name=role_name,
                                     error=str(e))
            return False
    
    def get_user_roles(self, user_id):
        """Get all roles assigned to user"""
        try:
            client_id = current_app.config['KEYCLOAK_CLIENT_ID']
            client = self.admin_client.get_client_id(client_id)
            
            # Get client roles
            client_roles = self.admin_client.get_client_roles_of_user(user_id, client)
            
            # Get realm roles
            realm_roles = self.admin_client.get_realm_roles_of_user(user_id)
            
            all_roles = []
            if client_roles:
                all_roles.extend([role['name'] for role in client_roles])
            if realm_roles:
                all_roles.extend([role['name'] for role in realm_roles])
            
            # Add debugging
            self.security_logger.debug("Retrieved user roles",
                                     operation="get_user_roles",
                                     component="keycloak_admin",
                                     user_id=user_id,
                                     client_roles=[role['name'] for role in client_roles] if client_roles else [],
                                     realm_roles=[role['name'] for role in realm_roles] if realm_roles else [],
                                     all_roles=all_roles)
            
            return all_roles
            
        except Exception as e:
            self.security_logger.error("Failed to get user roles",
                                     operation="get_user_roles",
                                     component="keycloak_admin",
                                     user_id=user_id,
                                     error=str(e))
            return []
    
    def set_user_password(self, user_id, password, temporary=True):
        """Set user password"""
        try:
            self.admin_client.set_user_password(user_id, password, temporary)
            
            self.audit_logger.info("User password set",
                                 operation="set_password",
                                 component="keycloak_admin",
                                 user_id=user_id,
                                 temporary=temporary)
            
            return True
            
        except Exception as e:
            self.security_logger.error("Failed to set user password",
                                     operation="set_password",
                                     component="keycloak_admin",
                                     user_id=user_id,
                                     error=str(e))
            return False

    def get_all_users(self):
        """Get all users from Keycloak"""
        try:
            users = self.admin_client.get_users()
            
            self.security_logger.info("Retrieved all users from Keycloak",
                                    operation="get_all_users",
                                    component="keycloak_admin",
                                    user_count=len(users))
            
            return users
            
        except Exception as e:
            self.security_logger.error("Failed to get users from Keycloak",
                                     operation="get_all_users",
                                     component="keycloak_admin",
                                     error=str(e))
            return []

    def get_users_by_role(self, role_name):
        """Get all users that have a specific role"""
        try:
            # Check if admin client is initialized
            if not self.admin_client:
                self.security_logger.error("Keycloak admin client not initialized",
                                         operation="get_users_by_role",
                                         component="keycloak_admin")
                return []
                
            all_users = self.get_all_users()
            if not all_users:
                self.security_logger.warning("No users found in Keycloak",
                                           operation="get_users_by_role",
                                           component="keycloak_admin",
                                           role_name=role_name)
                return []
                
            users_with_role = []
            
            for user in all_users:
                try:
                    user_roles = self.get_user_roles(user['id'])
                    if role_name in user_roles:
                        # Add role information to user object
                        user['roles'] = user_roles
                        users_with_role.append(user)
                except Exception as user_error:
                    self.security_logger.warning("Error getting roles for user",
                                                operation="get_users_by_role",
                                                component="keycloak_admin",
                                                user_id=user.get('id'),
                                                username=user.get('username'),
                                                error=str(user_error))
                    continue
            
            self.security_logger.info("Retrieved users by role from Keycloak",
                                    operation="get_users_by_role",
                                    component="keycloak_admin",
                                    role_name=role_name,
                                    total_users_checked=len(all_users),
                                    users_with_role=len(users_with_role))
            
            return users_with_role
            
        except Exception as e:
            self.security_logger.error("Failed to get users by role from Keycloak",
                                     operation="get_users_by_role",
                                     component="keycloak_admin",
                                     role_name=role_name,
                                     error=str(e))
            return []

    def get_laboratorista_users(self):
        """Get all users with laboratorista role"""
        try:
            # Check if admin client is initialized
            if not self.admin_client:
                self.security_logger.error("Keycloak admin client not initialized",
                                         operation="get_laboratorista_users",
                                         component="keycloak_admin")
                return []
                
            laboratorista_role = current_app.config.get('KEYCLOAK_TECNICO_ROLE', 'laboratorista')
            users = self.get_users_by_role(laboratorista_role)
            
            self.security_logger.info("Retrieved laboratorista users",
                                    operation="get_laboratorista_users",
                                    component="keycloak_admin",
                                    user_count=len(users),
                                    role_name=laboratorista_role)
            
            return users
            
        except Exception as e:
            self.security_logger.error("Failed to get laboratorista users",
                                     operation="get_laboratorista_users",
                                     component="keycloak_admin",
                                     error=str(e))
            return []

    def sync_users_to_local_db(self):
        """Sync Keycloak users with laboratorista role to local database"""
        try:
            # Check if admin client is initialized
            if not self.admin_client:
                self.security_logger.error("Keycloak admin client not initialized",
                                         operation="sync_users",
                                         component="keycloak_admin")
                raise Exception("Keycloak admin client not initialized")
            
            try:
                from app.models.models import db, Usuario
                from app.utils.keycloak_auth import map_keycloak_roles_to_app_roles
            except ImportError as e:
                self.security_logger.error("Failed to import required modules",
                                         operation="sync_users",
                                         component="keycloak_admin",
                                         error=str(e))
                raise Exception(f"Import error: {str(e)}")
            
            # Get all laboratorista users from Keycloak
            keycloak_users = self.get_laboratorista_users()
            
            # Add debugging
            self.audit_logger.info("Starting user synchronization",
                                 operation="sync_users",
                                 component="keycloak_admin",
                                 total_users_found=len(keycloak_users))
            
            sync_stats = {
                'created': 0,
                'updated': 0,
                'skipped': 0,
                'errors': 0
            }
            
            for kc_user in keycloak_users:
                try:
                    # Extract user data
                    user_id = kc_user.get('username') or kc_user.get('id')
                    email = kc_user.get('email')
                    first_name = kc_user.get('firstName', '')
                    last_name = kc_user.get('lastName', '')
                    
                    # Skip if essential data is missing
                    if not user_id or not email:
                        self.security_logger.warning("Skipping user with missing essential data",
                                                    operation="sync_users",
                                                    component="keycloak_admin",
                                                    keycloak_user_id=kc_user.get('id'),
                                                    username=user_id,
                                                    email=email)
                        sync_stats['skipped'] += 1
                        continue
                    
                    # Map Keycloak roles to app roles
                    kc_roles = kc_user.get('roles', [])
                    app_roles = map_keycloak_roles_to_app_roles(kc_roles)
                    
                    # Extract primary role (ensure it's a string, not a list)
                    if isinstance(app_roles, list):
                        primary_role = app_roles[0] if app_roles else 'tecnico'
                    else:
                        primary_role = app_roles if app_roles else 'tecnico'
                    
                    # Check if user already exists
                    existing_user = Usuario.query.filter(
                        (Usuario.idUsuario == user_id) | (Usuario.email == email)
                    ).first()
                    
                    if existing_user:
                        # Update existing user
                        existing_user.nombre = first_name
                        existing_user.apellido = last_name
                        existing_user.email = email
                        existing_user.rol = primary_role
                        
                        sync_stats['updated'] += 1
                        
                        self.audit_logger.info("Updated user from Keycloak sync",
                                             operation="sync_users",
                                             component="keycloak_admin",
                                             user_id=user_id,
                                             action="updated")
                    else:
                        # Create new user
                        new_user = Usuario(
                            idUsuario=user_id,
                            nombre=first_name,
                            apellido=last_name,
                            email=email,
                            rol=primary_role
                        )
                        
                        # Set a temporary password - user will use Keycloak for authentication
                        new_user.set_password('keycloak_managed')
                        
                        db.session.add(new_user)
                        sync_stats['created'] += 1
                        
                        self.audit_logger.info("Created user from Keycloak sync",
                                             operation="sync_users",
                                             component="keycloak_admin",
                                             user_id=user_id,
                                             action="created")
                
                except Exception as user_error:
                    self.security_logger.error("Error processing user during sync",
                                             operation="sync_users",
                                             component="keycloak_admin",
                                             keycloak_user_id=kc_user.get('id'),
                                             error=str(user_error))
                    sync_stats['errors'] += 1
                    continue
            
            # Commit all changes
            db.session.commit()
            
            self.audit_logger.info("User synchronization completed",
                                 operation="sync_users",
                                 component="keycloak_admin",
                                 stats=sync_stats)
            
            return sync_stats
            
        except Exception as e:
            db.session.rollback()
            self.security_logger.error("Failed to sync users from Keycloak",
                                     operation="sync_users",
                                     component="keycloak_admin",
                                     error=str(e))
            raise

# Create global instance
keycloak_admin = KeycloakAdminClient()
