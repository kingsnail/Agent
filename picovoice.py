print("picovoice.py")
import pvporcupine
from   pvrecorder import PvRecorder
import record_speech
import command_parser
import os
import openai
from   elevenlabslib import *
## Setup for Eleven Labs Speech Generation
user_11labs = ElevenLabsUser(os.getenv("ELEVEN_LABS_USER")
voice       = user_11labs.get_voices_by_name("Rachel")[0]  # This is a list because multiple voices can have the same name

## Setup for Porcupine wakeword detection
keywords_list      = ['picovoice', 'bumblebee']
keyword_path_list  = ['Dumb-ass_en_windows_v2_2_0.ppn']
keyword_path_names = ['Dumb Ass']

porcupine = pvporcupine.create(
    access_key   = porcupine_access_key,
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
        keyword_index = porcupine.process(recorder.read())
        if keyword_index >= 0:
            print(f"Detected {keyword_path_names[keyword_index]}")
            recorder.stop()
            
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
                voice.generate_and_play_audio(r, playInBackground=False)
                if exit_flag:
                    working = False
                else:                    
                    print("Next...")
            recorder.start()
except KeyboardInterrupt:
    recorder.stop()
except Exception as e: 
    print("Something went wrong: ")
    print(e)
finally:
    porcupine.delete()
    recorder.delete()
    print("Stopped.")

