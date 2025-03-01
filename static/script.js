async function fetchForecast() {
    try {
        let response = await fetch('/forecast');
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        let data = await response.json();
        console.log("API Response:", data);  // Debugging

        if (data.error) {
            alert("Error fetching data: " + data.error);
            return;
        }

        // Extract dates, solar energy, and wind energy from API response
        const labels = data.map(entry => entry.date_time);
        const solarEnergy = data.map(entry => entry.sunlight_intensity);
        const windEnergy = data.map(entry => entry.wind_speed);

        const ctx = document.getElementById("forecastChart").getContext("2d");
        new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,  // Dates
                datasets: [
                    {
                        label: "Solar Energy",
                        data: solarEnergy,
                        borderColor: "orange",
                        backgroundColor: "rgba(255, 165, 0, 0.2)",
                        fill: true
                    },
                    {
                        label: "Wind Energy",
                        data: windEnergy,
                        borderColor: "blue",
                        backgroundColor: "rgba(0, 0, 255, 0.2)",
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    x: { title: { display: true, text: "Date & Time" } },
                    y: { title: { display: true, text: "Energy (MW)" } }
                }
            }
        });

    } catch (error) {
        console.error("Fetch error:", error);
        alert("Error fetching forecast data. Check console for details.");
    }
}

window.onload = fetchForecast;
