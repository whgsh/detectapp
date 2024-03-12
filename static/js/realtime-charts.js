document.addEventListener('DOMContentLoaded', function() {
    // 初始化 Chart.js 图表
    const amplitudeCtx = document.getElementById('amplitudeChart').getContext('2d');
    const frequencyCtx = document.getElementById('frequencyChart').getContext('2d');
    
   
   
  
      
    const amplitudeChart = new Chart(amplitudeCtx, {
        type: 'line',
        data: {
            labels: [],  // 时间标签
            datasets: [{
                label: 'Amplitude',
                data: [],
                fill: false,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'second',
                        tooltipFormat: 'HH:mm:ss'
                    },
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: true
                }
            }
        }
    });


    const frequencyChart = new Chart(frequencyCtx, {
        type: 'line',
        data: {
            labels: [],  // 时间标签
            datasets: [{
                label: 'Frequency',
                data: [],
                fill: false,
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1
            }]
        },
        options: {
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'second',
                        tooltipFormat: 'HH:mm:ss'
                    },
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: true
                }
            }
        }
    });
 

function updateData() {
    fetch('/data')
        .then(response => response.json())
        .then(data => {
            const currentTime = new Date().toLocaleTimeString();
            const maxDataPoints = 60; // 假设每5秒更新一次，60个数据点代表5*60=300秒，即5分钟
            const timeWindow = 60 * 1000; // 60秒的时间窗口
            const now = Date.now();

            // 更新振幅图表数据
            const amplitudeData = amplitudeChart.data.datasets[0].data;
            const amplitudeLabels = amplitudeChart.data.labels;

            // 更新频率图表数据
            const frequencyData = frequencyChart.data.datasets[0].data;
            const frequencyLabels = frequencyChart.data.labels;

            // 添加新数据
            amplitudeData.push({ x: now, y: data.amplitude });
            frequencyData.push({ x: now, y: data.frequency });

            // 移除超出60秒窗口的数据点
            while (amplitudeData.length > 0 && amplitudeData[0].x < now - timeWindow) {
                amplitudeData.shift();
            }
            while (frequencyData.length > 0 && frequencyData[0].x < now - timeWindow) {
                frequencyData.shift();
            }

            // 移除对应的标签
            while (amplitudeLabels.length > 0 && amplitudeLabels[0] < now - timeWindow) {
                amplitudeLabels.shift();
            }
            while (frequencyLabels.length > 0 && frequencyLabels[0] < now - timeWindow) {
                frequencyLabels.shift();
            }

            // 更新图表
            amplitudeChart.update();
            frequencyChart.update();

            document.getElementById('amplitudeValue').textContent = data.amplitude.toFixed(2); // 保留两位小数
            document.getElementById('frequencyValue').textContent = data.frequency.toFixed(2); 
        })
        .catch(error => console.error('Error fetching data:', error));
}

setInterval(updateData, 5000);
   
});