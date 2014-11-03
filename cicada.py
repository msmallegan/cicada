# cicada.py
#
# Goal: Output tone that gradually changes to match the loudest other
# tone being heard.
#

import pyaudio
import time
import wave
from subprocess import call
import os
import scipy

# Hopefully these will be compatible with most microphone setups
WIDTH = 2
CHANNELS = 1
RATE = 44100
CHUNK = 1024

def saveWave(data,filename='output.wav'):
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(WIDTH)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()

def detectPitch(data):
    """
    Returns an estimate of the dominant pitch in Hz
    given PyAudio data.

    Requires aubio command-line tool 'aubiopitch'.
    http://aubio.org/
    """
    # 10.30.2014 At the moment, this (inefficiently!)
    # saves the data to a wave file and then runs
    # 'aubiopitch' on it.
    # This is ultra-clunky.  I am coding on an airplane :)

    tmpPrefix = 'detectPitch_tmp'+str(os.getpid())

    tmpWaveName = tmpPrefix+'.wav'
    saveWave(data,tmpWaveName)

    tmpPitchName = tmpPrefix+'.txt'
    tmpPitchFile = open(tmpPitchName,'w')
    try:
        call(["aubiopitch","-i",tmpWaveName],
             stdout=tmpPitchFile)
    except OSError, e:
        raise Exception, "Problem calling aubiopitch: "+str(e)
    tmpPitchFile.close()

    tmpPitchFile = open(tmpPitchName,'r')
    # takes penultimate line of output as current pitch
    lines = tmpPitchFile.readlines()
    pitchList = [ float(line.split()[-1]) for line in lines ]
    pitch = pitchList[-2]

    # If I ever registered silence, don't report a pitch.
    # (Avoids noise / partially heard sounds?)
    if scipy.any(scipy.array(pitchList)[:-1]==0.):
        pitch = 0.

    # debug
    #print ""
    #print pitchList

    # clean up
    os.remove(tmpPitchName)
    os.remove(tmpWaveName)

    return pitch

def playTone(pitch,time=1):
    """
    Plays sinusoidal tone of given pitch (in Hz)
    for given time (in seconds).
    """
    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(WIDTH),
                    channels=CHANNELS,
                    rate=RATE,
                    output=True)
    floatData = scipy.sin( scipy.pi*float(pitch)/RATE* \
        scipy.arange(int(time*RATE)))
    chrData = [ chr(int(scipy.floor(d*127.+128.))) \
        for d in floatData ]
    stream.write(b''.join(chrData))
    stream.stop_stream()
    stream.close()

    p.terminate()

def wire():
    """
    Simple example of input audio -> output audio.
    """
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

        #pitch = detectPitch(in_data)
        #print pitch

        return (out_data, pyaudio.paContinue)

    stream = p.open(format=p.get_format_from_width(WIDTH),
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    output=True,
                    stream_callback=callback)

    stream.start_stream()

    while stream.is_active():
        time.sleep(1)

    stream.stop_stream()
    stream.close()

    p.terminate()

def audioInput(samples=2048):
    """
    Return audio data from input channel (microphone).
    By default, returns two "chunks" of 1024 samples
    (This seems to be just enough to get a stable estimate
    of the pitch.)
    """
    # 10.28.2014 Example taken from 'Wire (Callback)'
    # at http://people.csail.mit.edu/hubert/pyaudio/
    #
    # At the moment it just outputs the audio it hears.
    # Careful for feedback :)

    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(WIDTH),
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []

    for i in range(0,int(samples / CHUNK)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    return b''.join(frames)

def mapToInterval(pitch,minPitch=220.,maxPitch=440.):
    """
    Given an arbitrary pitch, find the equivalent note
    within the given pitch range (which by default spans
    one octave).
    """
    log = scipy.log

    logIntervalRange = log(maxPitch) - log(minPitch)
    d = (log(pitch)-log(minPitch)) % logIntervalRange
    mappedPitch = scipy.exp(log(minPitch) + d)

    return mappedPitch

def simpleCicada(learningRate=0.5,toneDur=(0.5,1.5),
    initialPitch=440.,minPitchIn=0.,maxPitchIn=2000.,
    minPitchOut=220.,maxPitchOut=440.):
    """
    If a pitch is heard, change myPitch according to
        myPitch *= (heardPitch/myPitch)**learningRate.

    Tone is played for a random time in the range given
    by toneDur (in seconds).

    Returns list of heard pitches and list of played pitches
    (in Hz).
    """
    myPitch = initialPitch
    heardPitchList,myPitchList = [],[]

    try:
        while True:
            # listen
            heardPitch = detectPitch(audioInput())

            # change
            if (heardPitch > minPitchIn) and (heardPitch < maxPitchIn):
                mappedPitch = mapToInterval(heardPitch,
                                minPitchOut,maxPitchOut)
                myPitch *= (mappedPitch/myPitch)**learningRate
            else:
                mappedPitch = 0.
            print "heardPitch = %.1f, mappedPitch = %.1f, myPitch = %.1f"%(heardPitch,mappedPitch,myPitch)

            # sing
            dur = toneDur[0] \
                + (toneDur[1]-toneDur[0])*scipy.random.rand()
            playTone(myPitch,dur)

            # log
            heardPitchList.append(heardPitch)
            myPitchList.append(myPitch)

    except KeyboardInterrupt:
        return heardPitchList,myPitchList


if __name__ == '__main__':

    heardPitchList,myPitchList = simpleCicada()



