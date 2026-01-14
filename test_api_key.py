"""Test script to verify OpenRouter API key is working."""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_key():
    """Test the OpenRouter API key with a simple request."""
    api_key = os.getenv("OPENROUTER_API_KEY")

    print("="*60)
    print("OpenRouter API Key Test")
    print("="*60)

    # Check if key exists
    if not api_key:
        print("❌ ERROR: OPENROUTER_API_KEY not found in .env file")
        return False

    # Show key (partially masked for security)
    masked_key = api_key[:8] + "..." + api_key[-8:] if len(api_key) > 16 else "***"
    print(f"✓ API Key found: {masked_key}")
    print(f"✓ Key length: {len(api_key)} characters")

    # Test the API
    print("\nTesting API connection...")
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",  # Optional but recommended
        "X-Title": "Medicare Guide Test"  # Optional but recommended
    }

    payload = {
        "model": "anthropic/claude-sonnet-4.5",
        "messages": [
            {"role": "user", "content": "Say 'API key is working!' in exactly those words."}
        ],
        "max_tokens": 50
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            message = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ SUCCESS! API is working!")
            print(f"Response: {message}")
            return True
        else:
            print(f"❌ ERROR: API request failed")
            print(f"Response: {response.text}")

            # Common error explanations
            if response.status_code == 401:
                print("\n💡 This usually means:")
                print("   - Your API key is invalid or expired")
                print("   - You need to get a new key from https://openrouter.ai/keys")
            elif response.status_code == 429:
                print("\n💡 This usually means:")
                print("   - You've hit rate limits")
                print("   - Your account may be out of credits")
            elif response.status_code == 402:
                print("\n💡 This usually means:")
                print("   - Your account needs credits")
                print("   - Add credits at https://openrouter.ai/credits")

            return False

    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to OpenRouter API")
        print("   Check your internet connection")
        return False
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = test_api_key()
    print("\n" + "="*60)
    if success:
        print("✅ Your API key is working correctly!")
    else:
        print("❌ Your API key is NOT working. See errors above.")
        print("\nNext steps:")
        print("1. Go to https://openrouter.ai/keys")
        print("2. Create a new API key")
        print("3. Update your .env file with the new key")
        print("4. Make sure you have credits: https://openrouter.ai/credits")
    print("="*60)
