from dotenv import load_dotenv
import os
import record_speech
import picovoice

# Load the .env file
load_dotenv()

# Access the environment variables
openai_irganization   = os.getenv("OPENAI_ORG")
openai_api_key        = os.getenv("OPENAI_API_KEY")
elevenlabs_user       = os.getenv("ELEVENLABS_USER")
elevenlabs_api_key    = os.getenv("ELEVENLABS_API_KEY")
elevenlabs_voice_1_id = os.getenv("ELEVENLABS_VOICE_1_ID")
porcupine_access_key  = os.getenv("PORCUPINE_ACCESS_KEY")

print("Starting...");
#record_speech.record_speech();
print("Complete.");
