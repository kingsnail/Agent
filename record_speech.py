import pyaudio
import wave

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
    
    

def record_speech():
    print("Recording speech...")
    # the file name output you want to record into
    filename = "speech.wav"
    # set the chunk size of 1024 samples
    chunk = 1024
    # sample format
    FORMAT = pyaudio.paInt16
    # mono, change to 2 if you want stereo
    channels = 1
    # device index on this system
    device_index = 1
    # 44100 samples per second
    sample_rate = 48000
    record_seconds = 10
    # initialize PyAudio object
    p = pyaudio.PyAudio()
    # open stream object as input & output
    print("Openning Stream...")
    stream = p.open(format=FORMAT,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    output=True,
                    frames_per_buffer=chunk,
                    input_device_index=device_index)
    print("Stream Open...")
    frames = []
    try:
        s_count   = 0
        n_count   = 0
        recording = True
        appending = False
        while(recording):
            data = stream.read(chunk)
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
        print("Finished recording.")
        
    # stop and close stream
    stream.stop_stream()
    stream.close()
    # terminate pyaudio object
    p.terminate()
    # save audio file
    # open the file in 'write bytes' mode
    wf = wave.open(filename, "wb")
    # set the channels
    wf.setnchannels(channels)
    # set the sample format
    wf.setsampwidth(p.get_sample_size(FORMAT))
    # set the sample rate
    wf.setframerate(sample_rate)
    # write the frames as bytes
    wf.writeframes(b"".join(frames))
    # close the file
    wf.close()
