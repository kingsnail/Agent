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
SPEECH_FILE_NAME   = "speech.wav"
CHUNK              = 1024
SAMPLE_FORMAT      = pyaudio.paInt16
CHANNELS           = 1                  # mono, change to 2 if you want stereo
INPUT_DEVICE_INDEX = 1
SAMPLE_RATE        = 48000

THRESHOLD     = 500
SILENT_CHUNKS = 100
NOISY_CHUNKS  = 20


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

try:
    print("Listening...")
    stream = p.open(format            = SAMPLE_FORMAT,
                    channels           = CHANNELS,
                    rate               = SAMPLE_RATE,
                    input              = True,
                    output             = False,
                    frames_per_buffer  = CHUNK,
                    input_device_index = INPUT_DEVICE_INDEX)
    print("Stream Open...")
  
    while True:
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
       
                except KeyboardInterrupt:
                    print("Keyboard Interrupt.")
                print("Finished recording.")
        
                stream.stop_stream()
                stream.close()
                # terminate pyaudio object
                p.terminate()
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
                r, exit_flag = command_parser.parse_command(transcript.text)       
                print("Command response was : ", r)
                audio_stream = tts_client.generate(
                    text="This is a... streaming voice!!",
                    stream=True
                    )

                stream(audio_stream)
                if exit_flag:
                    working = False
                else:                    
                    print("Next...")
            #recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
            #recorder.start()
except KeyboardInterrupt:
    recorder.stop()
except Exception as e: 
    print("Something went wrong: ")
    print(e)
finally:
    porcupine.delete()
    print("Stopped.")

