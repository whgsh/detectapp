document.addEventListener('DOMContentLoaded', function() {
    const amplitudeDisplay = document.getElementById('amplitude');
    const frequencyDisplay = document.getElementById('frequency');

    // Function to update amplitude and frequency
    function updateData() {
        fetch('/data')
            .then(response => response.json())
            .then(data => {
                amplitudeDisplay.textContent = data.amplitude.toFixed(2);
                frequencyDisplay.textContent = data.frequency.toFixed(2);
            })
            .catch(error => console.error('Error fetching data:', error));
    }

    // Update data every second
    setInterval(updateData, 1000);
});
