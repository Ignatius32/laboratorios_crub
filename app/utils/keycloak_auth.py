"""
Keycloak Authentication Utilities
Provides authentication decorators and user management functions
"""
from functools import wraps
from flask import session, redirect, url_for, flash, current_app
from flask_login import current_user, login_user, logout_user
from app.models.models import Usuario, db
from app.integrations.keycloak_oidc import keycloak_oidc
from app.integrations.keycloak_admin_client import keycloak_admin
from app.utils.logging_config import get_security_logger, get_audit_logger
from werkzeug.security import generate_password_hash
import uuid

class KeycloakAuth:
    """Keycloak authentication service"""
    
    def __init__(self):
        self.security_logger = get_security_logger()
        self.audit_logger = get_audit_logger()
    
    def map_keycloak_roles_to_app_roles(self, keycloak_roles):
        """Map Keycloak roles to application roles"""
        role_mapping = {
            current_app.config['KEYCLOAK_ADMIN_ROLE']: 'admin',
            current_app.config['KEYCLOAK_TECNICO_ROLE']: 'tecnico'
        }
        
        # Check for admin role first
        if current_app.config['KEYCLOAK_ADMIN_ROLE'] in keycloak_roles:
            return 'admin'
        elif current_app.config['KEYCLOAK_TECNICO_ROLE'] in keycloak_roles:
            return 'tecnico'
        else:
            # Default role
            return 'tecnico'
    
    def sync_user_from_keycloak(self, user_info, keycloak_roles):
        """Sync user from Keycloak to local database"""
        try:
            # Extract user information
            keycloak_id = user_info.get('sub')
            email = user_info.get('email')
            first_name = user_info.get('given_name', '')
            last_name = user_info.get('family_name', '')
            username = user_info.get('preferred_username', email)
            
            if not email or not keycloak_id:
                self.security_logger.error("Missing required user info from Keycloak",
                                         operation="sync_user",
                                         component="keycloak_auth",
                                         user_info=user_info)
                return None
            
            # Map roles
            app_role = self.map_keycloak_roles_to_app_roles(keycloak_roles)
            
            # Check if user exists
            user = Usuario.query.filter_by(email=email).first()
            
            if user:
                # Update existing user
                user.nombre = first_name
                user.apellido = last_name
                user.rol = app_role
                # Store Keycloak ID if not already stored
                if not hasattr(user, 'keycloak_id') or not user.keycloak_id:
                    # Add keycloak_id field if it doesn't exist
                    if not hasattr(Usuario, 'keycloak_id'):
                        # For now, we'll use the email as the identifier
                        pass
                
                self.audit_logger.info("User updated from Keycloak sync",
                                     operation="sync_user",
                                     component="keycloak_auth",
                                     user_id=user.idUsuario,
                                     email=email,
                                     role=app_role)
            else:
                # Create new user
                # Generate a unique user ID
                user_id = self._generate_user_id()
                
                user = Usuario(
                    idUsuario=user_id,
                    nombre=first_name,
                    apellido=last_name,
                    email=email,
                    telefono='',
                    password_hash=generate_password_hash(str(uuid.uuid4())),  # Random password, not used
                    rol=app_role
                )
                
                db.session.add(user)
                
                self.audit_logger.info("New user created from Keycloak sync",
                                     operation="sync_user",
                                     component="keycloak_auth",
                                     user_id=user_id,
                                     email=email,
                                     role=app_role)
            
            db.session.commit()
            return user
            
        except Exception as e:
            db.session.rollback()
            self.security_logger.error("Failed to sync user from Keycloak",
                                     operation="sync_user",
                                     component="keycloak_auth",
                                     error=str(e),
                                     user_info=user_info)
            return None
    
    def _generate_user_id(self):
        """Generate a unique user ID"""
        # Find the highest existing ID and increment
        last_user = db.session.query(Usuario).order_by(Usuario.idUsuario.desc()).first()
        if last_user and last_user.idUsuario.isdigit():
            return str(int(last_user.idUsuario) + 1).zfill(10)
        else:
            # Start from a base number if no numeric IDs exist
            return "1000000001"
    
    def login_user_from_keycloak(self, token):
        """Login user using Keycloak token"""
        try:
            # Get user info from token
            user_info = keycloak_oidc.get_user_info(token)
            if not user_info:
                self.security_logger.warning("No user info in Keycloak token",
                                           operation="keycloak_login",
                                           component="keycloak_auth")
                return False
            
            # Get user roles
            keycloak_roles = keycloak_oidc.get_user_roles(token)
            
            # Sync user to local database
            user = self.sync_user_from_keycloak(user_info, keycloak_roles)
            if not user:
                return False
            
            # Login user
            login_user(user, remember=True)
            
            # Mark as Keycloak authenticated
            session['keycloak_authenticated'] = True
            
            self.security_logger.info("User logged in via Keycloak",
                                    operation="keycloak_login",
                                    component="keycloak_auth",
                                    user_id=user.idUsuario,
                                    email=user.email)
            
            return True
            
        except Exception as e:
            self.security_logger.error("Failed to login user from Keycloak",
                                     operation="keycloak_login",
                                     component="keycloak_auth",
                                     error=str(e))
            return False
    
    def logout_user_from_keycloak(self):
        """Logout user and clear Keycloak session"""
        try:
            user_id = current_user.idUsuario if current_user.is_authenticated else None
            
            # Generate Keycloak logout URL BEFORE clearing session data
            # (logout_url() needs the token for id_token_hint)
            logout_url = keycloak_oidc.logout_url()
            
            # Clear Flask-Login session
            logout_user()
            
            # Clear Keycloak session data
            session.pop('keycloak_authenticated', None)
            session.pop('keycloak_token', None)
            
            self.security_logger.info("User logged out from Keycloak",
                                    operation="keycloak_logout",
                                    component="keycloak_auth",
                                    user_id=user_id)
            
            return logout_url
            
        except Exception as e:
            self.security_logger.error("Failed to logout user from Keycloak",
                                     operation="keycloak_logout",
                                     component="keycloak_auth",
                                     error=str(e))
            return url_for('main.index')
    
    def is_authenticated(self):
        """Check if user is authenticated via Keycloak"""
        if not session.get('keycloak_authenticated', False):
            return False
        
        token = session.get('keycloak_token')
        if not token:
            return False
            
        # Check if token is still valid
        return keycloak_oidc.is_token_valid(token)
    
    def require_keycloak_auth(self, f):
        """Decorator to require Keycloak authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.is_authenticated():
                flash('Por favor, inicie sesión para acceder a esta página.', 'info')
                return redirect(url_for('auth.keycloak_login'))
            return f(*args, **kwargs)
        return decorated_function
    
    def require_role(self, required_role):
        """Decorator to require specific role"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not current_user.is_authenticated:
                    flash('Por favor, inicie sesión para acceder a esta página.', 'info')
                    return redirect(url_for('auth.keycloak_login'))
                
                if current_user.rol != required_role and current_user.rol != 'admin':
                    flash('No tiene permisos para acceder a esta página.', 'error')
                    return redirect(url_for('main.index'))
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator

# Create global instance
keycloak_auth = KeycloakAuth()

def map_keycloak_roles_to_app_roles(keycloak_roles):
    """Global function to map Keycloak roles to application roles"""
    admin_role = current_app.config.get('KEYCLOAK_ADMIN_ROLE', 'app_admin')
    tecnico_role = current_app.config.get('KEYCLOAK_TECNICO_ROLE', 'laboratorista')
    
    # Check for admin role first
    if admin_role in keycloak_roles:
        return ['admin']
    elif tecnico_role in keycloak_roles:
        return ['tecnico']
    else:
        # Default role for users without specific roles
        return ['tecnico']
