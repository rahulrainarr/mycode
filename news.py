import feedparser
import requests
import json
import time

# === CONFIG ===
RSS_FEED_URL = "https://www.theverge.com/rss/index.xml"  # Replace with your favorite
LLM_API_URL = "http://localhost:1234/v1/chat/completions"  # LM Studio endpoint
ELEVENLABS_API_KEY = "your_elevenlabs_api_key_here"
VOICE_ID = "your_voice_id_here"  # Get from ElevenLabs dashboard
OUTPUT_FILE = "techcast.mp3"


# === STEP 1: Get Headlines ===
def fetch_headlines(limit=5):
    feed = feedparser.parse(RSS_FEED_URL)
    return [entry.title for entry in feed.entries[:limit]]


# === STEP 2: Summarize with LLM ===
def generate_script(headlines):
    prompt = f"""
You are a tech news podcaster. Turn these headlines into a natural 2–3 minute podcast script.
Make it friendly, engaging, and sound spoken aloud. Add intro + signoff.

Headlines:
{chr(10).join(['- ' + h for h in headlines])}
"""
    data = {
        "model": "mistral",  # or whatever you named your model
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }

    response = requests.post(LLM_API_URL, json=data)
    result = response.json()
    return result['choices'][0]['message']['content']


# === STEP 3: Generate TTS with ElevenLabs ===
def text_to_speech(text, output_path):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.75, "similarity_boost": 0.75}
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Podcast saved as: {output_path}")
    else:
        print(f"❌ Error: {response.status_code}, {response.text}")


# === MAIN ===
if __name__ == "__main__":
    print("🔍 Fetching headlines...")
    headlines = fetch_headlines()

    print("🧠 Generating podcast script...")
    script = generate_script(headlines)

    print("🎙️ Converting to speech...")
    text_to_speech(script, OUTPUT_FILE)
