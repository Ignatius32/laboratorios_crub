from app import create_app
from config import Config, DevelopmentConfig, ProductionConfig
import datetime
import os

# Determine configuration based on environment
env = os.environ.get('FLASK_ENV', 'development')
if env == 'production':
    config_class = ProductionConfig
elif env == 'development':
    config_class = DevelopmentConfig
else:
    config_class = Config

app = create_app(config_class)

@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

if __name__ == '__main__':
    # Only run in debug mode for development
    debug_mode = env == 'development'
    app.run(debug=debug_mode)