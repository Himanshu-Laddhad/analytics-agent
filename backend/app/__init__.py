from pathlib import Path
from dotenv import load_dotenv
import os

# Try to load .env from multiple locations
backend_env = Path(__file__).parent.parent / ".env"
root_env = Path(__file__).parent.parent.parent / ".env"

if backend_env.exists():
    load_dotenv(dotenv_path=backend_env, override=True)
    print(f"✅ Loaded .env from: {backend_env}")
elif root_env.exists():
    load_dotenv(dotenv_path=root_env, override=True)
    print(f"✅ Loaded .env from: {root_env}")
else:
    print(f"⚠️  Warning: No .env file found!")
    print(f"   Looked in: {backend_env}")
    print(f"   Looked in: {root_env}")
    print(f"   Using environment variables if available")