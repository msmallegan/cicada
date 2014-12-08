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
import pianoputer
from scipy.io import wavfile

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

def loadWave(filename):
    fps, sound = wavfile.read(filename)
    #wf = wave.Wave_read(filename)
    #sound = wf.readframes(wf.getnframes())
    # if there is more than one channel, only return first one
    # (doesn't seem to work at the moment for stereo case...)
    if len(scipy.shape(sound)) > 1:
        return sound[:,1]
    else:
        return sound

def detectPitch(data,verbose=False):
    """
    Returns an estimate of the dominant pitch in Hz
    given PyAudio data.

    Requires aubio command-line tool 'aubiopitch'.
    http://aubio.org/
    
    If a long audio sample is given, uses two 
    "chunks" of 1024 samples in the middle of the
    sample.
    """
    # take data from the middle of the sample
    N = len(data)
    if N > 2048:
        middleData = data[N/2-1024:N/2+1024]
    else:
        middleData = data
    
    # 10.30.2014 At the moment, this (inefficiently!)
    # saves the data to a wave file and then runs
    # 'aubiopitch' on it.
    # This is ultra-clunky.  I am coding on an airplane :)

    tmpPrefix = 'detectPitch_tmp'+str(os.getpid())

    tmpWaveName = tmpPrefix+'.wav'
    saveWave(middleData,tmpWaveName)

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

    if verbose:
        print "detectPitch: ",pitchList

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

def playSound(soundArray,originalPitch=1.,newPitch=1.):
    """
    Plays input array as a sound, optionally shifting
    its pitch.
    """
    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(WIDTH),
                    channels=CHANNELS,
                    rate=RATE,
                    output=True)
    
    # calculate pitch shift in semitones
    # to work with pianoputer
    n = 12. * scipy.log2(newPitch/originalPitch)
    shiftedArray = pianoputer.pitchshift(soundArray,n)
    
    stream.write(shiftedArray)
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

def recordSound(dur=1.):
    """
    User-friendly sound input.
    
    Counts down, then records sound for given
    duration (in seconds).  Repeats until
    a pitch is heard, then returns the recorded
    sound.
    """
    
    pitch = 0.
    while pitch == 0.:
        # countdown
        for i in range(3,0,-1):
            print i
            time.sleep(1.)

        # record sound
        print "Recording..."
        data = audioInput(int(RATE*dur))
        
        # um... something wrong with the format.
        # try writing to file and reading back in.
        tmpPrefix = 'recordSound_tmp'+str(os.getpid())
        tmpWaveName = tmpPrefix+'.wav'
        saveWave(data,tmpWaveName)
        data = loadWave(tmpWaveName)
        os.remove(tmpWaveName)
        
        # check for pitch
        pitch = detectPitch(data)
        if pitch == 0.:
            print "Couldn't hear you.  Try again:"

    return data

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

def simpleCicada(sound,learningRate=0.5,waitDur=(0.,0.5),
    initialPitch=880.,minPitchIn=0.,maxPitchIn=2000.,
    minPitchOut=880.,maxPitchOut=1760.):
    """
    If a pitch is heard, change myPitch according to
        myPitch *= (heardPitch/myPitch)**learningRate.

    Between sounds, wait a random time in the range given
    by waitDur (in seconds).

    Returns list of heard pitches and list of played pitches
    (in Hz).
    """
    myPitch = initialPitch
    heardPitchList,myPitchList = [],[]

    # measure pitch of audio sample
    samplePitch = detectPitch(sound)
    print "samplePitch = %.1f"%samplePitch

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
            #playTone(myPitch,dur)
            playSound(sound,samplePitch,myPitch)

            # log
            curTime = time.time()
            heardPitchList.append([curTime,heardPitch])
            myPitchList.append([curTime,myPitch])

            # wait
            dur = waitDur[0] \
                + (waitDur[1]-waitDur[0])*scipy.random.rand()
            time.sleep(dur)

    except KeyboardInterrupt:
        # save data to file
        prefix = str(os.getpid())
        scipy.savetxt(prefix+'pitchList.txt',myPitchList)
        return heardPitchList,myPitchList


if __name__ == '__main__':

    # () choose sound to use
    #
    # Use this line to record a sound to use.
    #sound = recordSound()
    #
    # Use this line to load a wave file
    #sound = loadWave("trumpet.wav")
    sound = loadWave("bowl.wav")
    #sound = loadWave("trombone.wav")
    #sound = loadWave("clarinet.wav")
    
    # () run cicada algorithm
    heardPitchList,myPitchList = simpleCicada(sound)



