"""
Keycloak Configuration for CRUB Laboratory Management System
"""
import os
from flask import current_app

class KeycloakConfig:
    """Centralized Keycloak configuration"""
    
    @staticmethod
    def get_oidc_config():
        """Get OpenID Connect configuration"""
        return {
            'client_id': current_app.config['KEYCLOAK_CLIENT_ID'],
            'client_secret': current_app.config['KEYCLOAK_CLIENT_SECRET'],
            'server_metadata_url': f"{current_app.config['KEYCLOAK_SERVER_URL']}realms/{current_app.config['KEYCLOAK_REALM']}/.well-known/openid-configuration",
            'client_kwargs': {
                'scope': 'openid email profile'
            }
        }
    
    @staticmethod
    def get_admin_config():
        """Get admin client configuration"""
        return {
            'server_url': current_app.config['KEYCLOAK_SERVER_URL'],
            'realm_name': current_app.config['KEYCLOAK_REALM'],
            'client_id': current_app.config['KEYCLOAK_CLIENT_ID'],
            'client_secret': current_app.config['KEYCLOAK_CLIENT_SECRET'],
            'verify': True
        }
    
    @staticmethod
    def get_role_mapping():
        """Get role mapping configuration"""
        return {
            'admin_role': current_app.config['KEYCLOAK_ADMIN_ROLE'],
            'tecnico_role': current_app.config['KEYCLOAK_TECNICO_ROLE']
        }
    
    @staticmethod
    def get_redirect_uris():
        """Get redirect URIs"""
        return {
            'redirect_uri': current_app.config['KEYCLOAK_REDIRECT_URI'],
            'post_logout_redirect_uri': current_app.config['KEYCLOAK_POST_LOGOUT_REDIRECT_URI']
        }
