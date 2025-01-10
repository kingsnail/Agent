from dotenv import load_dotenv
import os
import record_speech;

# Load the .env file
load_dotenv()

# Access the environment variables
openai_api_key        = os.getenv("OPENAI_API_KEY")
elevenlabs_api_key    = os.getenv("ELEVENLABS_API_KEY")
elevenlabs_voice_1_id = os.getenv("ELEVENLABS_VOICE_1_ID")

print("Starting...");
record_speech.record_speech();
print("Complete.");
