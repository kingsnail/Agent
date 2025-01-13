print("voice_agent.py")
from dotenv import load_dotenv
import os
import struct

import pyaudio
import wave
import pvporcupine
import command_parser
import os
import time
from   openai import OpenAI

## Load the .env file
print("Loading environment variables...")
load_dotenv()

# the file name output you want to record into
SPEECH_FILE_NAME    = "speech.wav"
CHUNK               = 1024
SAMPLE_FORMAT       = pyaudio.paInt16
CHANNELS            = 1                  # mono, change to 2 if you want stereo
INPUT_DEVICE_INDEX  = 1
OUTPUT_DEVICE_INDEX = 0
SAMPLE_RATE         = 48000

THRESHOLD     = 500  # Threshold value for silence in the input audio stream
SILENT_CHUNKS = 100  # Number of chunks of silence needed to establish a pause
NOISY_CHUNKS  = 20   # Minimum noisy chunks allowed


import numpy as np
from scipy.signal import resample_poly

def downsample_48k_to_16k(raw_pcm_data):
    # Convert bytes to int16 array
    samples_48k = np.frombuffer(raw_pcm_data, dtype=np.int16)
    
    # Downsample from 48k to 16k => factor of 1/3
    samples_16k = resample_poly(samples_48k, up=1, down=3)
    
    # Convert to int16 to match what Porcupine expects
    samples_16k = samples_16k.astype(np.int16)

    # Return as a NumPy array (Porcupine can process an array or list of ints)
    return samples_16k
    
def get_max(d):
    m = 0
    for i in range(0, len(d), 2):
        b = d[i:i+2]
        v = int.from_bytes(b, "little", signed="True")
        #print(str(d[i]) + " + " + str(d[i+1]) + " = " + str(v))
        if abs(v) > m:
             m = abs(v)
    return m
    
# initialize PyAudio object
print("Instantiate PyAudio...")
p = pyaudio.PyAudio()

print("Initialize OpenAI API...")
openai = OpenAI()

print("Initialize PicoVoice...")
## Setup for Porcupine wakeword detection
keywords_list      = ['picovoice', 'bumblebee']
keyword_path_list  = ['Dumb-Ass_en_raspberry-pi_v3_0_0.ppn']
keyword_path_names = ['Dumb Ass']

porcupine = pvporcupine.create(
    access_key   = os.getenv("PORCUPINE_ACCESS_KEY"),
    #keywords    = keywords_list,
    keyword_paths= keyword_path_list
)

input_stream_open  = False
output_stream_open = False

try:
    print("Listening...")
    if input_stream_open == False:
        stream = p.open(format            = SAMPLE_FORMAT,
                        channels           = CHANNELS,
                        rate               = SAMPLE_RATE,
                        input              = True,
                        output             = False,
                        frames_per_buffer  = CHUNK,
                        input_device_index = INPUT_DEVICE_INDEX)
        input_stream_open = True
        print("Stream Open...")
  
    while True:
        if stream.is_active() == False:
            stream.start_stream()
        pcm = stream.read(porcupine.frame_length * 3)        
        data16k = downsample_48k_to_16k(pcm)
        # Process the audio frame with Porcupine
        keyword_index = porcupine.process(data16k)

        if keyword_index >= 0:
            print(f"Detected {keyword_path_names[keyword_index]}")
            ## The keyword has been recognized. So now we are awake, capture speech.
            working = True
            while working:
                ## Now record the speech that follows the wake word...
                #record_speech.record_speech()

                frames = []
                try:
                    s_count   = 0
                    n_count   = 0
                    recording = True
                    appending = False
                    if stream.is_active() == False:
                        stream.start_stream()
                    while(recording):
                        data = stream.read(CHUNK)
                        # Detect a silent frame
                        if get_max(data) < THRESHOLD:
                           s_count += 1
                           print("n_count=", str(n_count), ", s_count=", str(s_count))
                           # Look for enough silent frames occuring AFTER a noisy period to stop recording
                           if (s_count > SILENT_CHUNKS) and (n_count > NOISY_CHUNKS):
                              recording = False
                              print("Stopped recording.")
                        else:
                           # This is a noisy frame
                           n_count  += 1
                           s_count   = 0
                           if not appending:
                               print("Recording - press Ctrl-c to stop...")
                               appending = True # Start adding to the recorded data now
                           if appending:
                               frames.append(data)
                    print("n_count = ", n_count)
                    print("s_count = ", s_count)
                except KeyboardInterrupt:
                    print("Keyboard Interrupt.")
                print("Finished recording.")
        
                stream.stop_stream()
                #stream.close()
                # save audio file
                # open the file in 'write bytes' mode
                wf = wave.open(SPEECH_FILE_NAME, "wb")
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(SAMPLE_FORMAT))
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(b"".join(frames))
                wf.close()

                ## Transcribe the captured text
                print("Transcribing...")
                audio_file = open(SPEECH_FILE_NAME, "rb")

                # Create transcription from audio file into English
                transcription = openai.audio.transcriptions.create(
                                    model    = "whisper-1",
                                    file     = audio_file,
                                    language = "en",
                                    )
                print("You said:")
                print(transcription.text)
                
                # Now decode the transcript to work out what action is to be taken.
                r, exit_flag = command_parser.parse_command(transcription.text)       
                print("Command response was : ", r)

                if output_stream_open == False:
                    player_stream = p.open(format              = SAMPLE_FORMAT,
                                           channels            = CHANNELS, 
                                           rate                = 24000, 
                                           input               = False,
                                           output              = True,
                                           output_device_index = OUTPUT_DEVICE_INDEX,
                                          )
                    output_stream_open = True
                    print("output stream open...")
                start_time = time.time()

                if player_stream.is_active() == False:
                    player_stream.start_stream()
                    
                with openai.audio.speech.with_streaming_response.create(
                    model           = "tts-1",
                    voice           = "alloy",
                    response_format = "pcm",  # similar to WAV, but without a header chunk at the start.
                    input           = r,
                    ) as response:
                        print(f"Time to first byte: {int((time.time() - start_time) * 1000)}ms")
                        for chunk in response.iter_bytes(chunk_size=2048):
                            #print("chunk")
                            player_stream.write(chunk)

                print(f"Done in {int((time.time() - start_time) * 1000)}ms.")
                player_stream.stop_stream()
                if exit_flag:
                    working = False
                else:                    
                    print("Next...")
except KeyboardInterrupt:
    if player_stream.is_active():
        player_stream.stop_stream()
    if stream.is_active():
        stream.stop_stream()
except Exception as e: 
    print("Something went wrong: ")
    print(e)
finally:
    porcupine.delete()
    print("Stopped.")

