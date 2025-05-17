#!/usr/bin/env python3
"""
Quick sanity-check for an OpenAI API key.
Save as `test_openai_key.py`, then run:
    export OPENAI_API_KEY="sk-..."
    python test_openai_key.py
"""

import os
import sys
import openai
from openai import OpenAI
from openai._exceptions import AuthenticationError, APIError, APIConnectionError, RateLimitError
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# 1️⃣  Grab the key.
api_key = os.getenv("OPENAI_API_KEY")
print(f"API key: {api_key}")
if not api_key or api_key.startswith("sk-paste"):
    sys.exit("❌  No API key found. Set OPENAI_API_KEY or paste it above.")

# 2️⃣  Configure client.
client = OpenAI(api_key=api_key)

try:
    # Lightweight endpoint to verify auth.
    response = client.models.list()
    model_id = response.data[0].id if response.data else "no models?"
    print(f"✅  Key works! First model returned: {model_id}")

except AuthenticationError as e:
    print("❌  Authentication failed: check that your key is correct and active.")
    print(e)
except RateLimitError:
    print("⚠️  Key is valid, but you're hitting a rate limit—try again later.")
except (APIError, APIConnectionError) as e:
    print("⚠️  Network or API error—key may be fine, but the service is unreachable.")
    print(e)
except Exception as e:
    print("⚠️  Unexpected error. Details:")
    raise
