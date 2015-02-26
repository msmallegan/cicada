

// d3.scale.category20()
var d3colors = ['#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c', '#98df8a', '#d62728', '#ff9896', '#9467bd', '#c5b0d5', '#8c564b', '#c49c94', '#bcbd22', '#dbdb8d', '#17becf', '#9edae5', '#e377c2', '#f7b6d2', '#7f7f7f', '#c7c7c7'];

function locationToGroup(x, y) {
    // Assign users based on even/odd ID.
    return (y + 9 * x ) % 2;
}

function locationToColor(x, y) {
    // 8 is the multiplier since we have 9 columns (x=1..9)
    var idx = (y + 9 * x) % d3colors.length;
    return d3colors[idx];
}
