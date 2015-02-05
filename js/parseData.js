// Requires jQuery and deque.js to be loaded.

"use strict";

var freqData = {};
(function (context) {

    var session = 'hi';
    var capacity = 5;
    var URL = "http://droova.com/python/cicada_view.py"

    // Fetch the last row id, synchronously.
    var last_row;
    $.ajax({
        url: URL,
        dataType: "json",
        async: false,
        data: {session: session, row_id: "last"},
        success: function(output) {
            last_row = output['last_row']
        }
    });

    // Get data since the last row id.
    context.queues = {};
    context.refresh = function refresh(heatmap, width, height, xMax, yMax) {
        $.ajax({
            url: URL,
            dataType: "json",
            async: true,
            data: {session: session, row_id: last_row},
            success: function(x) {
                if (x.length > 0) {
                    last_row = x[0][0];
                }
                context.updateData(x);
                var means = context.calculateMeans(x, width, height, xMax, yMax);
                if (means.length > 0) {
                    console.log(means[0].value);
                }
                heatmap.setData({
                    min: minFreq,
                    max: maxFreq,
                    data: means
                });
                heatmap.repaint();
            },
        });
    }
 
    // For use in plot/index.html
    context.refreshPlot = function refreshPlot(data) {
        $.ajax({
            url: URL,
            dataType: "json",
            async: true,
            data: {session: session, row_id: last_row},
            success: function(x) {
                if (x.length > 0) {
                    last_row = x[0][0];
                }
                context.updateData(x);
                var means = context.calculateMeans(x,1,1,1,1);
                if (means.length > 0) {
                    //console.log(means);
                    var d = [];
                    // Loop over cicadas
                    for (var i=0; i < means.length; i++){
                        d.push(means[i].value);
                    }
                    data.push(d);
                    //console.log(d);
                }
            },
        });
    }

    context.updateData = function (data) {

        // id, session, location, date sent, date received, frequency_in, frequency_out
        var queues = context.queues;
        var dataLength = data.length;

        // First push all the data.
        for (var i = 0; i < dataLength; i++) {
            var row = data[i];
            var loc = row[2];
            var freq = row[6];
            if (!(loc in queues)) {
                queues[loc] = new Deque(capacity);
                // Store the actual location (as an Array)
                queues[loc].location = loc;
            }

            var que = queues[loc];
            while (que._length >= capacity) {
                que.shift();
            }
            que.push(freq)
        }

    }

    context.calculateMean = function (data) {
        var dataLength = data._length; // this is a deque object!
        var mean = 0;
        var count = 0;
        for (var i = 0; i < dataLength; i++) {
            // null is treated numerically as 0.
            // Need to adjust this if we have NaNs.
            mean += data.get(i); // this is a deque object!
            count += 1;
        }
        return mean / count;
    };

    context.calculateMeans = function (data, width, height, xMax, yMax) {

        // id, session, location, date sent, date received, frequency_in, frequency_out
        var queues = context.queues;

        var xScale = width / xMax;
        var yScale = height / yMax;

        // Update the means
        var means = [];
        for (var loc in queues) {
            if (queues.hasOwnProperty(loc)) {
                var que = queues[loc];
                //console.log(que);
                var mean = context.calculateMean(que);
                var obj = {
                    x: que.location[0] * xScale,
                    y: height - que.location[1] * yScale,
                    value: mean,
                }
                //console.log(obj);
                means.push(obj);
            }
        }

        return means;
    };

})(freqData);
