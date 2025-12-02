import requests



# Read the actual text from your file
with open("final_script.txt", "r") as file:
    script_text = file.read()

url = "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL"

data = {
    "text": script_text,
    "model": "eleven_multilingual_v2",
    "voice_settings": {"stability": 0.20, "similarity_boost": 0.75}
}

headers = {
    "xi-api-key": ELEVEN_API_KEY,
    "Accept": "audio/mpeg"
}

response = requests.post(url, json=data, headers=headers)

# Save result audio
with open("narration.mp3", "wb") as f:
    f.write(response.content)

print("Audio saved as narration.mp3")