// Function to trigger energy prediction on login
async function triggerPrediction() {
    try {
        let response = await fetch('/predict', { method: 'GET' });
        let data = await response.json();

        console.log("Prediction response:", data); // Debugging log

        if (data.error) {
            console.error("Prediction failed:", data.error);
            alert("Prediction failed: " + data.error);
            return false;
        }

        console.log("Prediction completed:", data);
        return true;

    } catch (error) {
        console.error("Error in prediction request:", error);
        alert("Error predicting energy data.");
        return false;
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
    let predictionSuccess = await triggerPrediction(); // ✅ Ensure prediction completes first

    if (predictionSuccess) {
        await fetchForecast(); // ✅ Fetch only if prediction succeeded
    } else {
        console.error("Prediction failed. Skipping forecast fetch.");
    }
}

// Function to handle login submission
async function handleLogin(event) {
    event.preventDefault(); // Prevent default form submission

    let formData = new FormData(document.getElementById("loginForm"));
    let response = await fetch("/login", {
        method: "POST",
        body: formData
    });

    if (response.redirected) {
        console.log("Login successful, triggering prediction...");
        await triggerPrediction(); // ✅ Predict immediately after login
        window.location.href = response.url; // Redirect to dashboard
    } else {
        let text = await response.text();
        alert("Login failed: " + text);
    }
}

// Attach login event listener
document.addEventListener("DOMContentLoaded", function () {
    let loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", handleLogin);
    } else {
        console.log("Not on login page, initializing dashboard...");
        initializeDashboard(); // Auto-fetch on dashboard load
    }
});
