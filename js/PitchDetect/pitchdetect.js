/*
The MIT License (MIT)

Copyright (c) 2014 Chris Wilson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/



window.AudioContext = window.AudioContext || window.webkitAudioContext;

var audioContext = null;
var isPlaying = false;
var sourceNode = null;
var analyser = null;
var theBuffer = null;
var DEBUGCANVAS = null;
var mediaStreamSource = null;
var haveAudioPermission = false;
var detectorElem,
    canvasElem,
    waveCanvas,
    pitchElem,
    noteElem,
    detuneElem,
    detuneAmount;

window.onload = function() {
    audioContext = new AudioContext();
    MAX_SIZE = Math.max(4,Math.floor(audioContext.sampleRate/5000));    // corresponds to a 5kHz signal
    /* BCD 12.22.2014 commented out loading of whistling example
    var request = new XMLHttpRequest();
    request.open("GET", "../sounds/whistling3.ogg", true);
    request.responseType = "arraybuffer";
    request.onload = function() {
      audioContext.decodeAudioData( request.response, function(buffer) {
            theBuffer = buffer;
        } );
    }
    request.send();
    */

    detectorElem = document.getElementById( "detector" );
    canvasElem = document.getElementById( "output" );
    DEBUGCANVAS = document.getElementById( "waveform" );
    if (DEBUGCANVAS) {
        waveCanvas = DEBUGCANVAS.getContext("2d");
        waveCanvas.strokeStyle = "black";
        waveCanvas.lineWidth = 1;
    }
    pitchElem = document.getElementById( "pitch" );
    noteElem = document.getElementById( "note" );
    detuneElem = document.getElementById( "detune" );
    detuneAmount = document.getElementById( "detune_amt" );

    detectorElem.ondragenter = function () {
        this.classList.add("droptarget");
        return false; };
    detectorElem.ondragleave = function () { this.classList.remove("droptarget"); return false; };
    detectorElem.ondrop = function (e) {
        this.classList.remove("droptarget");
        e.preventDefault();
        theBuffer = null;

        var reader = new FileReader();
        reader.onload = function (event) {
            audioContext.decodeAudioData( event.target.result, function(buffer) {
                theBuffer = buffer;
            }, function(){alert("error loading!");} );

        };
        reader.onerror = function (event) {
            alert("Error: " + reader.error );
        };
        reader.readAsArrayBuffer(e.dataTransfer.files[0]);
        return false;
    };

    // BCD 12.23.2014 automatically start "live input" mode
    //toggleLiveInput();



}

function error() {
    alert('Stream generation failed.');
}

function getUserMedia(dictionary, callback) {
    if (!haveAudioPermission){
        $("#positionMessage").html("Click 'Allow' up above.").effect("shake");
        try {
            navigator.getUserMedia =
                navigator.getUserMedia ||
                navigator.webkitGetUserMedia ||
                navigator.mozGetUserMedia;
            navigator.getUserMedia(dictionary, callback, error);
        } catch (e) {
            alert('getUserMedia threw exception :' + e);
        }
    }
    else {
        callback();
    }
}

function gotStream(stream) {
    // Create an AudioNode from the stream.
    if (!haveAudioPermission)
        mediaStreamSource = audioContext.createMediaStreamSource(stream);

    // Connect it to the destination.
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048;
    mediaStreamSource.connect( analyser );
    updatePitch();

    // remember that we have gotten audio permission
    haveAudioPermission = true;

    document.getElementById("startStopButton").innerHTML= "Stop";
    $("#positionMessage").html("");
    $("#startStopButton").css("background", "#B51E41");
    isPlaying = true;

    // set initial pitch
    // initialPitch is now a slider....
    noteElem.innerText = $("#initialPitch").nstSlider('get_current_min_value');
    //noteElem.innerText = document.getElementById( "initialPitch" ).value;
}

/*
function toggleOscillator() {
    if (isPlaying) {
        //stop playing and return
        sourceNode.stop( 0 );
        sourceNode = null;
        analyser = null;
        isPlaying = false;
        if (!window.cancelAnimationFrame)
            window.cancelAnimationFrame = window.webkitCancelAnimationFrame;
        window.cancelAnimationFrame( rafID );
        return "play oscillator";
    }
    sourceNode = audioContext.createOscillator();

    analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048;
    sourceNode.connect( analyser );
    analyser.connect( audioContext.destination );
    sourceNode.start(0);
    isPlaying = true;
    isLiveInput = false;
    updatePitch();

    return "stop";
}
*/

function toggleLiveInput(makePaused) {
    $("#startStopButton").blur();

    if (typeof makePaused !== "undefined") {

        // Then this was called from the successfulSend, which means that
        // we want to change the state.
        if (isPaused) {
            // Nothing is playing, and we want to unpause.
            // We will simply make the button read "Start!" and be clickable.
            isPaused = false;
            isPlaying = false;

            // This only removes the on-the-fly style, it doesn't change the CSS.

            $("#startStopButton").removeAttr("style");
            $("#startStopButton").html("Start!");
            $("#startStopButton").prop('disabled', false);

            $("#positionMessage").html('Click "Start!" to begin again.');
            $("#positionMessage").effect("shake");


        }
        else {
            // Potentially, stuff might be playing, but either way, we want
            // to pause. We make the button read "Locked" and not clickable.
            isPaused = true;

            $("#positionMessage").html("");
            $("#startStopButton").css("background", "purple");
            $("#startStopButton").html("Disabled");
            $("#startStopButton").prop('disabled', true);

            detectorElem.className = "vague";
            analyser = null;
            isPlaying = false;
            if (!window.cancelAnimationFrame) {
                window.cancelAnimationFrame = window.webkitCancelAnimationFrame;
            }
            window.cancelAnimationFrame( rafID );
        }
    }
    else {
        if (isPlaying) {
            //stop playing and return
            //sourceNode.stop( 0 );
            //sourceNode = null;
            detectorElem.className = "vague";
            analyser = null;
            isPlaying = false;
            if (!window.cancelAnimationFrame)
                window.cancelAnimationFrame = window.webkitCancelAnimationFrame;
            window.cancelAnimationFrame( rafID );
            document.getElementById("startStopButton").innerHTML= "Start!";
            // This only removes the on-the-fly style, it doesn't change the CSS.
            $("#startStopButton").removeAttr("style");

        }

        else{
            // Do nothing unless location is set
            xloc = parseInt(document.getElementById( "xloc" ).value);
            yloc = parseInt(document.getElementById( "yloc" ).value);

            // Ask for microphone access
            if (xloc > -1 && yloc > -1) {
                getUserMedia(
                    {
                        "audio": {
                            "mandatory": {
                                "googEchoCancellation": "false",
                                "googAutoGainControl": "false",
                                "googNoiseSuppression": "false",
                                "googHighpassFilter": "false"
                            },
                            "optional": []
                        },
                    }, gotStream);
            }
            else {
                // Show warning to select positions.
                $("#positionMessage").html("Please specify your position.");
                $("#positionMessage").effect("shake");
            }
        } // end else
    } // end doSomething
}

/*
function togglePlayback() {
    if (isPlaying) {
        //stop playing and return
        sourceNode.stop( 0 );
        sourceNode = null;
        analyser = null;
        isPlaying = false;
        if (!window.cancelAnimationFrame)
            window.cancelAnimationFrame = window.webkitCancelAnimationFrame;
        window.cancelAnimationFrame( rafID );
        return "start";
    }

    sourceNode = audioContext.createBufferSource();
    sourceNode.buffer = theBuffer;
    sourceNode.loop = true;

    analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048;
    sourceNode.connect( analyser );
    analyser.connect( audioContext.destination );
    sourceNode.start( 0 );
    isPlaying = true;
    isLiveInput = false;
    updatePitch();

    return "stop";
}
*/

var rafID = null;
var tracks = null;
var buflen = 1024;
var buf = new Float32Array( buflen );

var noteStrings = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

function noteFromPitch( frequency ) {
    var noteNum = 12 * (Math.log( frequency / 440 )/Math.log(2) );
    return Math.round( noteNum ) + 69;
}

function frequencyFromNoteNumber( note ) {
    return 440 * Math.pow(2,(note-69)/12);
}

function centsOffFromPitch( frequency, note ) {
    return Math.floor( 1200 * Math.log( frequency / frequencyFromNoteNumber( note ))/Math.log(2) );
}

// this is a float version of the algorithm below - but it's not currently used.
/*
function autoCorrelateFloat( buf, sampleRate ) {
    var MIN_SAMPLES = 4;    // corresponds to an 11kHz signal
    var MAX_SAMPLES = 1000; // corresponds to a 44Hz signal
    var SIZE = 1000;
    var best_offset = -1;
    var best_correlation = 0;
    var rms = 0;

    if (buf.length < (SIZE + MAX_SAMPLES - MIN_SAMPLES))
        return -1;  // Not enough data

    for (var i=0;i<SIZE;i++)
        rms += buf[i]*buf[i];
    rms = Math.sqrt(rms/SIZE);

    for (var offset = MIN_SAMPLES; offset <= MAX_SAMPLES; offset++) {
        var correlation = 0;

        for (var i=0; i<SIZE; i++) {
            correlation += Math.abs(buf[i]-buf[i+offset]);
        }
        correlation = 1 - (correlation/SIZE);
        if (correlation > best_correlation) {
            best_correlation = correlation;
            best_offset = offset;
        }
    }
    if ((rms>0.1)&&(best_correlation > 0.1)) {
        console.log("f = " + sampleRate/best_offset + "Hz (rms: " + rms + " confidence: " + best_correlation + ")");
    }
//  var best_frequency = sampleRate/best_offset;
}
*/

var MIN_SAMPLES = 0;  // will be initialized when AudioContext is created.

function autoCorrelate( buf, sampleRate ) {
    var SIZE = buf.length;
    var MAX_SAMPLES = Math.floor(SIZE/2);
    var best_offset = -1;
    var best_correlation = 0;
    var rms = 0;
    var foundGoodCorrelation = false;
    var correlations = new Array(MAX_SAMPLES);

    for (var i=0;i<SIZE;i++) {
        var val = buf[i];
        rms += val*val;
    }
    rms = Math.sqrt(rms/SIZE);
    if (rms<0.01) // not enough signal
        return -1;

    var lastCorrelation=1;
    for (var offset = MIN_SAMPLES; offset < MAX_SAMPLES; offset++) {
        var correlation = 0;

        for (var i=0; i<MAX_SAMPLES; i++) {
            correlation += Math.abs((buf[i])-(buf[i+offset]));
        }
        correlation = 1 - (correlation/MAX_SAMPLES);
        correlations[offset] = correlation; // store it, for the tweaking we need to do below.
        if ((correlation>0.9) && (correlation > lastCorrelation)) {
            foundGoodCorrelation = true;
            if (correlation > best_correlation) {
                best_correlation = correlation;
                best_offset = offset;
            }
        } else if (foundGoodCorrelation) {
            // short-circuit - we found a good correlation, then a bad one, so we'd just be seeing copies from here.
            // Now we need to tweak the offset - by interpolating between the values to the left and right of the
            // best offset, and shifting it a bit.  This is complex, and HACKY in this code (happy to take PRs!) -
            // we need to do a curve fit on correlations[] around best_offset in order to better determine precise
            // (anti-aliased) offset.

            // we know best_offset >=1,
            // since foundGoodCorrelation cannot go to true until the second pass (offset=1), and
            // we can't drop into this clause until the following pass (else if).
            var shift = (correlations[best_offset+1] - correlations[best_offset-1])/correlations[best_offset];
            return sampleRate/(best_offset+(8*shift));
        }
        lastCorrelation = correlation;
    }
    if (best_correlation > 0.01) {
        // console.log("f = " + sampleRate/best_offset + "Hz (rms: " + rms + " confidence: " + best_correlation + ")")
        return sampleRate/best_offset;
    }
    return -1;
//  var best_frequency = sampleRate/best_offset;
}

function updatePitch( time ) {
    var cycles = new Array;
    analyser.getFloatTimeDomainData( buf );
    var ac = autoCorrelate( buf, audioContext.sampleRate );
    // TODO: Paint confidence meter on canvasElem here.

    if (DEBUGCANVAS) {  // This draws the current waveform, useful for debugging
        var xmax = 256; //512;
        var ymax = 64; //256;

        waveCanvas.clearRect(0,0,xmax,ymax);
        /*
        waveCanvas.strokeStyle = "red";
        waveCanvas.beginPath();
        waveCanvas.moveTo(0,0);
        waveCanvas.lineTo(0,256);
        waveCanvas.moveTo(128,0);
        waveCanvas.lineTo(128,256);
        waveCanvas.moveTo(256,0);
        waveCanvas.lineTo(256,256);
        waveCanvas.moveTo(384,0);
        waveCanvas.lineTo(384,256);
        waveCanvas.moveTo(512,0);
        waveCanvas.lineTo(512,256);
        waveCanvas.stroke();
        */

        waveCanvas.strokeStyle = "black";
        waveCanvas.strokeStyle = colorFunc(xylocation[0], xylocation[1]);
        waveCanvas.lineWidth = 3;
        waveCanvas.beginPath();
        waveCanvas.moveTo(0,ymax/2+buf[0]);
        for (var i=1;i<xmax;i++) {
            waveCanvas.lineTo(i,ymax/2+(buf[i]*ymax/2));
        }
        waveCanvas.stroke();
    }

    if (ac == -1) {
        //detectorElem.className = "vague";
        pitchElem.innerText = "--";
        //noteElem.innerText = "-";
        detuneElem.className = "";
        detuneAmount.innerText = "";
        pitch = NaN;
    } else {
        detectorElem.className = "confident";
        pitch = ac;
        pitchElem.innerText = Math.round( pitch ) ;
        //var note =  noteFromPitch( pitch );
        //noteElem.innerHTML = noteStrings[note%12];

        // BCD 12.23.2014 remove detuning text
        /*
        var detune = centsOffFromPitch( pitch, note );
        if (detune == 0 ) {
            detuneElem.className = "";
            detuneAmount.innerHTML = "--";
        } else {
            if (detune < 0)
                detuneElem.className = "flat";
            else
                detuneElem.className = "sharp";
            detuneAmount.innerHTML = Math.abs( detune );
        }
        */
    }

    if (!window.requestAnimationFrame)
        window.requestAnimationFrame = window.webkitRequestAnimationFrame;
    rafID = window.requestAnimationFrame( updatePitch );
}
