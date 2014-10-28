# cicada.py
#
# Goal: Output tone that gradually changes to match the loudest other
# tone being heard.
#

import pyaudio
import time

# Hopefully these will be compatible with most microphone setups
WIDTH = 2
CHANNELS = 1
RATE = 44100

if __name__ == '__main__':
    
    # 10.28.2014 Example taken from 'Wire (Callback)'
    # at http://people.csail.mit.edu/hubert/pyaudio/
    #
    # At the moment it just outputs the audio it hears.
    # Careful for feedback :)
    
    p = pyaudio.PyAudio()

    # The callback function is called repeatedly while the audio
    # stream is open.  in_data is the input audio
    def callback(in_data, frame_count, time_info, status):
        
        # Here's where we will analyze the in_data and use it
        # to calculate the out_data.  For now, do something simple.
        out_data = in_data
        
        return (out_data, pyaudio.paContinue)

    stream = p.open(format=p.get_format_from_width(WIDTH),
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    output=True,
                    stream_callback=callback)

    stream.start_stream()

    while stream.is_active():
        time.sleep(0.1)

    stream.stop_stream()
    stream.close()

    p.terminate()