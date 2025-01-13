#!/usr/bin/env rye run python

import time
from   pathlib import Path
from   dotenv  import load_dotenv
import os
from   openai  import OpenAI

# Load the .env file
print("Loading environment variables...")
load_dotenv()

# gets OPENAI_API_KEY from your environment variables
openai = OpenAI()

speech_file_path = Path(__file__).parent / "test_tran.wav"

def main() -> None:
    print("")
    print("")
    print("")
    print("")
    print("Starting")
    stream_to_speakers("The audio stream is working.")

    # Create text-to-speech audio file
    #with openai.audio.speech.with_streaming_response.create(
    #    model="tts-1",
    #    voice="alloy",
    #    input="the quick brown fox jumped over the lazy dogs",
    #) as response:
    #    response.stream_to_file(speech_file_path)

    print("Transcribing...")
    # Create transcription from audio file into English
    transcription = openai.audio.transcriptions.create(
        model    = "whisper-1",
        file     = speech_file_path,
        language = "en",
    )
    print("Transcription is :")
    print(transcription.text)

    # Create translation from audio file
    #translation = openai.audio.translations.create(
    #    model="whisper-1",
    #    file=speech_file_path,
    #)
    #print(translation.text)


def stream_to_speakers( text = "No stream text supplied.") -> None:
    import pyaudio
    p = pyaudio.PyAudio()
        
    player_stream = p.open(format=pyaudio.paInt16, 
                           channels=1, 
                           rate=24000, 
                           output=True,
                           output_device_index=0)

    start_time = time.time()

    with openai.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="alloy",
        response_format="pcm",  # similar to WAV, but without a header chunk at the start.
        input=text,
    ) as response:
        print(f"Time to first byte: {int((time.time() - start_time) * 1000)}ms")
        for chunk in response.iter_bytes(chunk_size=2048):
            #print("chunk")
            player_stream.write(chunk)

    print(f"Done in {int((time.time() - start_time) * 1000)}ms.")


if __name__ == "__main__":
    main()
