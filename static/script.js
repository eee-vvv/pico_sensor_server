const history = {{ history | tojson }};

const upstairs = history.filter(r => r.sensor_id === 'upstairs').reverse();
const downstairs = history.filter(r => r.sensor_id === 'downstairs').reverse();

new Chart(document.getElementById('tempChart'), {
    type: 'line',
    data: {
        datasets: [
            {
                label: 'Upstairs (°F)',
                data: upstairs.map(r => ({ x: r.timestamp, y: r.temperature })),
                borderColor: '#c0392b',
                backgroundColor: 'rgba(192,57,43,0.08)',
                tension: 0.3,
                fill: true,
            },
            {
                label: 'Downstairs (°F)',
                data: downstairs.map(r => ({ x: r.timestamp, y: r.temperature })),
                borderColor: '#2980b9',
                backgroundColor: 'rgba(41,128,185,0.08)',
                tension: 0.3,
                fill: true,
            }
        ]
    },
    options: {
        responsive: true,
        scales: {
            x: {
                type: 'category',
                ticks: { maxTicksLimit: 10, maxRotation: 45 }
            },
            y: {
                title: { display: true, text: 'Temperature (°F)' }
            }
        }
    }
});
