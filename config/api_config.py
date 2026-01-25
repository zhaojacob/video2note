"""
API key configuration and validation
"""
import os
from pathlib import Path


def load_env_vars():
    """Load environment variables from .env file if exists"""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def get_glm_api_key() -> str:
    """Get GLM API key from environment"""
    load_env_vars()
    api_key = os.getenv("GLM_API_KEY", "")
    if not api_key:
        raise ValueError(
            "GLM_API_KEY not found. Please set it in environment variables or .env file.\n"
            "You can get one from: https://open.bigmodel.cn/"
        )
    return api_key


def get_doubao_api_key() -> str:
    """Get Doubao API key from environment (ARK_API_KEY)"""
    load_env_vars()
    api_key = os.getenv("ARK_API_KEY", "")
    if not api_key:
        raise ValueError(
            "ARK_API_KEY not found. Please set it in environment variables or .env file.\n"
            "You can get one from: https://www.volcengine.com/"
        )
    return api_key


def validate_api_keys():
    """Validate that all required API keys are set"""
    try:
        get_glm_api_key()
        print("[OK] GLM API key is configured")
    except ValueError as e:
        print(f"[X] {e}")

    try:
        get_doubao_api_key()
        print("[OK] Doubao API key is configured")
    except ValueError as e:
        print(f"[X] {e}")


# Example .env file template
ENV_TEMPLATE = """# Video Note System - Environment Variables

# GLM-4.6V API Key
# Get from: https://open.bigmodel.cn/
GLM_API_KEY=your_glm_api_key_here

# Doubao API Key (Ark API)
# Get from: https://www.volcengine.com/docs/82379/1399008
ARK_API_KEY=your_ark_api_key_here

# Optional: HTTP Proxy
# HTTP_PROXY=http://127.0.0.1:7890
# HTTPS_PROXY=http://127.0.0.1:7890
"""


def create_env_template():
    """Create a .env template file if it doesn't exist"""
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(ENV_TEMPLATE)
        print(f"Created .env template at {env_file}")
        print("Please edit it with your API keys")
    else:
        print(f".env file already exists at {env_file}")


if __name__ == "__main__":
    create_env_template()
    validate_api_keys()
