var osc, envelope, fft;

/*
BCD 12.23.2014
Adapted from example at
http://p5js.org/learn/examples/Sound__Note_Envelope.php
*/

function mapToInterval( pitch,minPitch,maxPitch ) {
	/*
    Given an arbitrary pitch, find the equivalent note
    within the given pitch range (which by default spans
    one octave).
    */
    var logIntervalRange = Math.log(maxPitch) - Math.log(minPitch);
    var d = (Math.log(pitch)-Math.log(minPitch)) % logIntervalRange;
    if (pitch < minPitch) {
        var mappedPitch = Math.exp(Math.log(maxPitch) + d);
    }
    else {
        var mappedPitch = Math.exp(Math.log(minPitch) + d);
    }

    return mappedPitch;
}

var s = function( sketch ) {

    var scaleArray = [60, 62, 64, 65, 67, 69, 71, 72];
    var note = 0;
    
    var minPitchOut = 880.;
    var maxPitchOut = 1760.;
    
    var maxPitchIn = 2000.;
    
    var learningRate = 0.5;

    sketch.setup = function() {
      sketch.createCanvas(710, 200);
      osc = new p5.SinOsc();

      // Instantiate the envelope with time / value pairs
      envelope = new p5.Env(0.01, 0.5, 1, 0.5);

      //osc.start();

      fft = new p5.FFT();
      sketch.noStroke();
    };

    sketch.draw = function() {
      sketch.background(20);
      
      // BCD 12.23.2014 wait for sound input to start and location to be set
      var active = false;
      detectorElem = document.getElementById( "detector" );
      if (detectorElem) {
        active = (detectorElem.className == "confident");
      }
      
      if (active) {
          // (*) Play myPitch
          if (sketch.frameCount % 60 == 0) {
            //var midiValue = scaleArray[note];
            //var freqValue = sketch.midiToFreq(midiValue);
            // BCD 12.23.2014
            var myPitch = Math.round( noteElem.innerHTML );
            var freqValue = myPitch;
            osc.freq(freqValue);

            envelope.play(osc);
            note = (note + 1) % scaleArray.length;
            
            // Send data to server
            sendData();
          }
          
          // (*) update myPitch between playing output notes
          if (sketch.frameCount % 60 == 59) {
            var heardPitch = pitch;
            if (heardPitch < maxPitchIn) {
                var mappedPitch = mapToInterval(heardPitch,minPitchOut,maxPitchOut);
                //var mappedPitch = heardPitch;
                var myPitchOld = Math.round( noteElem.innerHTML );
                var myPitch = myPitchOld * Math.pow(mappedPitch/myPitchOld,learningRate);
                // Use PitchDetect's 'noteElem' text to display current output
                noteElem.innerHTML = Math.round( myPitch );
            }
          }
      }

      // plot FFT.analyze() frequency analysis on the canvas 
      var spectrum = fft.analyze();
      for (var i = 0; i < spectrum.length/20; i++) {
        sketch.fill(spectrum[i], spectrum[i]/10, 0);
        var x = sketch.map(i, 0, spectrum.length/20, 0, sketch.width);
        var h = sketch.map(spectrum[i], 0, 255, 0, sketch.height);
        sketch.rect(x, sketch.height, spectrum.length/20, -h);
      }
    };
};

var myp5 = new p5(s);