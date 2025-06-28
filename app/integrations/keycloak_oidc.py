"""
Keycloak OpenID Connect Integration for Flask Application
Handles OAuth2/OIDC authentication flows
"""
from authlib.integrations.flask_client import OAuth
from flask import current_app, session, url_for, redirect, request, flash
from flask_login import login_user, logout_user
import jwt
from jwt.exceptions import InvalidTokenError
import requests
from urllib.parse import urlencode
from app.utils.logging_config import get_security_logger

class KeycloakOIDC:
    """Handles Keycloak OpenID Connect authentication"""
    
    def __init__(self, app=None):
        self.oauth = OAuth()
        self.keycloak = None
        self.logger = get_security_logger()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.oauth.init_app(app)
        
        # Ensure server URL ends with /
        server_url = app.config['KEYCLOAK_SERVER_URL']
        if not server_url.endswith('/'):
            server_url = server_url + '/'
            app.config['KEYCLOAK_SERVER_URL'] = server_url
        
        try:
            # Register Keycloak client
            self.keycloak = self.oauth.register(
                name='keycloak',
                client_id=app.config['KEYCLOAK_CLIENT_ID'],
                client_secret=app.config['KEYCLOAK_CLIENT_SECRET'],
                server_metadata_url=f"{server_url}realms/{app.config['KEYCLOAK_REALM']}/.well-known/openid-configuration",
                client_kwargs={
                    'scope': 'openid email profile'
                }
            )
            
            self.logger.info("Keycloak OIDC client initialized successfully",
                            operation="keycloak_init",
                            component="keycloak_oidc",
                            realm=app.config['KEYCLOAK_REALM'],
                            server_url=server_url)
                            
        except Exception as e:
            self.logger.error("Failed to initialize Keycloak OIDC client",
                            operation="keycloak_init",
                            component="keycloak_oidc",
                            error=str(e),
                            server_url=server_url,
                            realm=app.config['KEYCLOAK_REALM'])
            raise
    
    def authorize_redirect(self):
        """Initiate OAuth2 authorization flow"""
        redirect_uri = current_app.config['KEYCLOAK_REDIRECT_URI']
        
        self.logger.info("Initiating OAuth2 authorization",
                        operation="oauth_authorize",
                        component="keycloak_oidc",
                        redirect_uri=redirect_uri)
        
        return self.keycloak.authorize_redirect(redirect_uri)
    
    def authorize_access_token(self):
        """Exchange authorization code for access token"""
        try:
            token = self.keycloak.authorize_access_token()
            
            # Validate token
            if not token:
                self.logger.warning("No token received from Keycloak",
                                  operation="token_exchange",
                                  component="keycloak_oidc")
                return None
            
            # Store token in server-side session (now safe due to Flask-Session)
            session['keycloak_token'] = token
            session['keycloak_authenticated'] = True
            
            self.logger.info("Access token obtained successfully",
                           operation="token_exchange",
                           component="keycloak_oidc",
                           token_type=token.get('token_type', 'unknown'),
                           token_size=len(str(token)))
            
            return token
            
        except Exception as e:
            self.logger.error("Failed to exchange authorization code for token",
                            operation="token_exchange",
                            component="keycloak_oidc",
                            error=str(e))
            return None
    
    def get_user_info(self, token):
        """Get user information from Keycloak"""
        try:
            # Log token structure for debugging
            self.logger.info("Getting user info from token",
                           operation="get_user_info",
                           component="keycloak_oidc",
                           token_keys=list(token.keys()) if token else [],
                           has_id_token=bool(token.get('id_token') if token else False),
                           has_access_token=bool(token.get('access_token') if token else False))
            
            # Try multiple methods to extract user info
            user_info = None
            
            # Method 1: Try to parse ID token using authlib
            try:
                user_info = self.keycloak.parse_id_token(token)
                if user_info:
                    self.logger.info("User info retrieved via parse_id_token",
                                   operation="get_user_info",
                                   component="keycloak_oidc",
                                   user_id=user_info.get('sub'),
                                   user_email=user_info.get('email'),
                                   user_name=user_info.get('name'))
                    return user_info
            except Exception as e:
                self.logger.warning("Failed to parse ID token with authlib",
                                  operation="get_user_info",
                                  component="keycloak_oidc",
                                  error=str(e),
                                  error_type=type(e).__name__)
            
            # Method 2: Manually decode ID token
            try:
                id_token = token.get('id_token')
                if id_token:
                    # Decode without verification for user info extraction
                    user_info = jwt.decode(
                        id_token,
                        options={"verify_signature": False, "verify_aud": False}
                    )
                    
                    if user_info:
                        self.logger.info("User info retrieved via manual JWT decode",
                                       operation="get_user_info",
                                       component="keycloak_oidc",
                                       user_id=user_info.get('sub'))
                        return user_info
            except Exception as e:
                self.logger.warning("Failed to manually decode ID token",
                                  operation="get_user_info",
                                  component="keycloak_oidc",
                                  error=str(e))
            
            # Method 3: Call userinfo endpoint
            try:
                access_token = token.get('access_token')
                if access_token:
                    userinfo_url = f"{current_app.config['KEYCLOAK_SERVER_URL']}/realms/{current_app.config['KEYCLOAK_REALM']}/protocol/openid-connect/userinfo"
                    headers = {'Authorization': f"Bearer {access_token}"}
                    
                    response = requests.get(userinfo_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        user_info = response.json()
                        self.logger.info("User info retrieved via userinfo endpoint",
                                       operation="get_user_info",
                                       component="keycloak_oidc",
                                       user_id=user_info.get('sub'))
                        return user_info
            except Exception as e:
                self.logger.warning("Failed to get user info from userinfo endpoint",
                                  operation="get_user_info",
                                  component="keycloak_oidc",
                                  error=str(e))
            
            # If all methods fail
            self.logger.error("All methods failed to extract user info",
                            operation="get_user_info",
                            component="keycloak_oidc")
            return None
            
        except Exception as e:
            self.logger.error("Failed to get user info from token",
                            operation="get_user_info",
                            component="keycloak_oidc",
                            error=str(e))
            return None
    
    def get_user_roles(self, token):
        """Extract user roles from token"""
        try:
            # Decode the access token to get roles
            access_token = token.get('access_token')
            if not access_token:
                return []
            
            # Decode token without verification for role extraction
            # Note: In production, you should verify the token
            decoded_token = jwt.decode(
                access_token, 
                options={"verify_signature": False, "verify_aud": False}
            )
            
            # Extract roles from resource_access or realm_access
            roles = []
            
            # Check client-specific roles
            client_id = current_app.config['KEYCLOAK_CLIENT_ID']
            if 'resource_access' in decoded_token and client_id in decoded_token['resource_access']:
                client_roles = decoded_token['resource_access'][client_id].get('roles', [])
                roles.extend(client_roles)
            
            # Check realm roles
            if 'realm_access' in decoded_token:
                realm_roles = decoded_token['realm_access'].get('roles', [])
                roles.extend(realm_roles)
            
            self.logger.info("User roles extracted from token",
                           operation="get_user_roles",
                           component="keycloak_oidc",
                           roles=roles)
            
            return roles
            
        except Exception as e:
            self.logger.error("Failed to extract roles from token",
                            operation="get_user_roles",
                            component="keycloak_oidc",
                            error=str(e))
            return []
    
    def logout_url(self, redirect_uri=None):
        """Generate logout URL"""
        if not redirect_uri:
            redirect_uri = current_app.config['KEYCLOAK_POST_LOGOUT_REDIRECT_URI']
        
        logout_endpoint = f"{current_app.config['KEYCLOAK_SERVER_URL']}/realms/{current_app.config['KEYCLOAK_REALM']}/protocol/openid-connect/logout"
        
        params = {
            'post_logout_redirect_uri': redirect_uri,
            'client_id': current_app.config['KEYCLOAK_CLIENT_ID']
        }
        
        # Add id_token_hint if available
        token = session.get('keycloak_token')
        if token and 'id_token' in token:
            params['id_token_hint'] = token['id_token']
        
        logout_url = f"{logout_endpoint}?{urlencode(params)}"
        
        self.logger.info("Logout URL generated",
                        operation="generate_logout_url",
                        component="keycloak_oidc",
                        redirect_uri=redirect_uri)
        
        return logout_url
    
    def is_token_valid(self, token):
        """Check if token is still valid"""
        try:
            if not token:
                return False
            
            access_token = token.get('access_token')
            if not access_token:
                return False
            
            # Decode token to check expiration
            decoded_token = jwt.decode(
                access_token, 
                options={"verify_signature": False, "verify_exp": True}
            )
            
            return True
            
        except InvalidTokenError:
            self.logger.warning("Token validation failed",
                              operation="validate_token",
                              component="keycloak_oidc")
            return False
        except Exception as e:
            self.logger.error("Error validating token",
                            operation="validate_token",
                            component="keycloak_oidc",
                            error=str(e))
            return False

# Create global instance
keycloak_oidc = KeycloakOIDC()
