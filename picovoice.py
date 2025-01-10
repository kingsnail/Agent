print("picovoice.py")
import pvporcupine
from   pvrecorder import PvRecorder
import record_speech
import command_parser
import os
import time
import openai
from elevenlabs.client import ElevenLabs
from elevenlabs import stream

## Setup for Eleven Labs Speech Generation
tts_client = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"), 
)
##voice       = user_11labs.get_voices_by_name("Rachel")[0]  # This is a list because multiple voices can have the same name

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
            time.sleep(5)
            ## The keyword has been recognized. So now we are awake, capture speech.
            working = True
            while working:
                record_speech.record_speech()
                print("Transcribing...")
                audio_file = open("speech.wav", "rb")
                transcript = openai.Audio.transcribe(model = "whisper-1", 
                                                     file   = audio_file,
                                                     temperature = 0.0,
                                                     language    = "en"
                                                     )
                print("You said:")
                print(transcript.text)
                
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

