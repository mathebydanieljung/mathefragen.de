var config = {
    type: 'line',
    data: {
        labels: this_year_months,
        datasets: [{
            label: 'qwd',
            backgroundColor: '#000',
            borderColor: '#030',
            fill: false,
            data: [
                12, 12, 12, 13, 11, 34, 21, 67, 54, 33, 45, 78
            ],
        }]
    },
    options: {
        title: {
            display: false,
            text: ''
        },
        legend: {
            display: false
        },
        scales: {
            xAxes: [{
                type: 'category',
                time: {
                    format: 'MM.YYYY'
                },
                scaleLabel: {
                    display: true,
                    labelString: 'Monate'
                }
            }],
            yAxes: [{
                scaleLabel: {
                    display: true,
                    labelString: 'Punkte'
                }
            }]
        },
    }
};

window.onload = function () {
    var ctx = document.getElementById('reputation_progress').getContext('2d');
    window.myLine = new Chart(ctx, config);
};