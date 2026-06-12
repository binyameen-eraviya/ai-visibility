import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    class DevelopmentConfig:
        DEBUG        : bool = False
        VERBOSE      : bool = True
        LOGS_DIR     : str  = "./logs"
        LOG_LEVEL    : str  = "INFO"
        TESTING_MODE : bool = False

    class ProductionConfig:
        DEBUG        : bool = False
        VERBOSE      : bool = True
        LOGS_DIR     : str  = "./logs"
        LOG_LEVEL    : str  = "INFO"
        TESTING_MODE : bool = False

    class ENV:
        is_development = "development" == os.getenv("APP_ENV", "development")
        is_production = not is_development

    if ENV.is_production:
        AppConfig = ProductionConfig
    else:
        AppConfig = DevelopmentConfig
