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

speech_file_path = Path(__file__).parent / "speech.mp3"


def main() -> None:
    print("Starting")
    stream_to_speakers()

    # Create text-to-speech audio file
    #with openai.audio.speech.with_streaming_response.create(
    #    model="tts-1",
    #    voice="alloy",
    #    input="the quick brown fox jumped over the lazy dogs",
    #) as response:
    #    response.stream_to_file(speech_file_path)

    # Create transcription from audio file
    #transcription = openai.audio.transcriptions.create(
    #    model="whisper-1",
    #    file=speech_file_path,
    #)
    #print(transcription.text)

    # Create translation from audio file
    #translation = openai.audio.translations.create(
    #    model="whisper-1",
    #    file=speech_file_path,
    #)
    #print(translation.text)


def stream_to_speakers() -> None:
    import pyaudio
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"Device index {i}: {info['name']}")
        print(f"  Max input channels : {info['maxInputChannels']}")
        print(f"  Max output channels: {info['maxOutputChannels']}")
        print("------")
        
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
        input="""I see skies of blue and clouds of white
                The bright blessed days, the dark sacred nights
                And I think to myself
                What a wonderful world""",
    ) as response:
        print(f"Time to first byte: {int((time.time() - start_time) * 1000)}ms")
        for chunk in response.iter_bytes(chunk_size=2048):
            #print("chunk")
            player_stream.write(chunk)

    print(f"Done in {int((time.time() - start_time) * 1000)}ms.")


if __name__ == "__main__":
    main()
