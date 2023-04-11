const ctx = document.getElementById('myChart').getContext('2d');

const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [], // Will be populated with timestamps
        datasets: [
            {
                label: 'Speed (kmph)',
                data: [], // Will be populated with speed values
                borderColor: 'rgba(75, 192, 192, 1)',
                tension: 0.1,
            },
            {
                label: 'Resistance',
                data: [], // Will be populated with resistance values
                borderColor: 'rgba(255, 99, 132, 1)',
                tension: 0.1,
            },
        ],
    },
options: {
    scales: {
        x: {
            type: 'time',
            time: {
                unit: 'second',
                displayFormats: {
                    second: 'h:mm:ss a'
                }
            },
            display: true,
            title: {
                display: true,
                text: 'Timestamp'
            }
        },
        y: {
            beginAtZero: true,
            display: true,
            title: {
                display: true,
                text: 'Value'
            }
        },
    },
},

});

function addDataPoint(speed, resistance, timestamp) {
    chart.data.labels.push(timestamp);
    chart.data.datasets[0].data.push(speed);
    chart.data.datasets[1].data.push(resistance);
    chart.update();
}

(async () => {
    const response = await fetch('/get_data');
    const data = await response.json();

    for (const point of data) {
        const { kmph, resistance, timestamp } = point;
        addDataPoint(kmph, resistance, timestamp);
    }
})();

