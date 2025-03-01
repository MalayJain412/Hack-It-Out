// Function to trigger prediction before fetching forecast data
async function triggerPrediction() {
    try {
        let response = await fetch('/predict', { method: 'GET' }); // ✅ Change to GET
        let data = await response.json();

        if (data.error) {
            console.error("Prediction Error:", data.error);
            alert("Prediction failed: " + data.error);
            return false; // Stop execution if prediction fails
        }

        console.log("Prediction data received:", data);
        return true; // Continue only if prediction is successful

    } catch (error) {
        console.error("Error triggering prediction:", error);
        alert("Error predicting energy data.");
        return false; // Stop execution
    }
}

// Function to fetch forecast data and update chart
async function fetchForecast() {
    try {
        let response = await fetch('/dashboard-data');
        let data = await response.json();

        if (!data.solar || !data.wind) {
            console.error("Invalid forecast data:", data);
            alert("No forecast data available.");
            return;
        }

        // Extracting data for the chart
        const dates = data.solar.map(entry => entry.date);
        const solarValues = data.solar.map(entry => entry.energy);
        const windValues = data.wind.map(entry => entry.energy);

        // Get the canvas element
        const ctx = document.getElementById("forecastChart").getContext("2d");

        // Destroy existing chart if it exists (to prevent duplication)
        if (window.myChart) {
            window.myChart.destroy();
        }

        // Create a new Chart instance
        window.myChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: dates,
                datasets: [
                    {
                        label: "Solar Energy (MW)",
                        data: solarValues,
                        backgroundColor: "orange",
                        borderColor: "orange",
                        fill: false
                    },
                    {
                        label: "Wind Energy (MW)",
                        data: windValues,
                        backgroundColor: "blue",
                        borderColor: "blue",
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

    } catch (error) {
        console.error("Fetch error:", error);
        alert("Error fetching forecast data.");
    }
}

// Function to initialize the dashboard
async function initializeDashboard() {
    let predictionSuccess = await triggerPrediction(); // ✅ Ensure prediction completes

    if (predictionSuccess) {
        await fetchForecast(); // ✅ Fetch only if prediction succeeded
    } else {
        console.error("Prediction failed. Skipping forecast fetch.");
    }
}

// Load dashboard data when page loads
// window.onload = initializeDashboard;
