print("voice_agent.py")
from dotenv import load_dotenv
import os


import pvporcupine
from   pvrecorder import PvRecorder
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

## Create the recorder for Porcupine
recorder = PvRecorder(device_index=-1, 
                      frame_length=porcupine.frame_length
)

try:
    print("Listening...")
    recorder.start()
  
    while True:
        #print("reading...")
        keyword_index = porcupine.process(recorder.read())
        if keyword_index >= 0:
            print(f"Detected {keyword_path_names[keyword_index]}")
            recorder.stop()
            recorder.delete()
            print("Recorder deleted.")
            time.sleep(1)
            ## The keyword has been recognized. So now we are awake, capture speech.
            working = True
            while working:
                ## Now record the speech that follows the wake word...
                #record_speech.record_speech()




                
                ## Transcribe the captured text
                print("Transcribing...")
                audio_file = open("speech.wav", "rb")

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
    recorder.delete()
    print("Stopped.")

