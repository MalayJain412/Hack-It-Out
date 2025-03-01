async function fetchForecast() {
    try {
        let response = await fetch('/dashboard-data'); 
        let data = await response.json();

        const dates = data.solar.map(entry => entry.date);
        const solarValues = data.solar.map(entry => entry.energy);
        const windValues = data.wind.map(entry => entry.energy);

        const ctx = document.getElementById("forecastChart").getContext("2d");
        new Chart(ctx, {
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
                maintainAspectRatio: false
            }
        });

    } catch (error) {
        console.error("Fetch error:", error);
        alert("Error fetching forecast data.");
    }
}

window.onload = fetchForecast;
