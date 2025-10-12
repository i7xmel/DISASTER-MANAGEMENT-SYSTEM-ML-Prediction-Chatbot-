document.addEventListener("DOMContentLoaded", function () {
    // Hotspot functionality
    const hotspotButton = document.getElementById("hotspot-button");
    const hotspotTable = document.getElementById("hotspotTable");
    
    if (hotspotTable) {
        if (hotspotButton) {
            hotspotButton.addEventListener("click", fetchHotspots);
        } else {
            console.error("⚠️ Hotspot button not found.");
        }
    }

    // Disaster Risk functionality
    const disasterRiskButton = document.getElementById("checkDisasterRisk");
    if (disasterRiskButton) {
        disasterRiskButton.addEventListener("click", getUserLocationForDisaster);
    } else {
        console.error("⚠️ Disaster risk button not found.");
    }
});

// 🔹 Fetch and display hotspot data
function fetchHotspots() {
    const hotspotTable = document.getElementById("hotspotTable");
    if (!hotspotTable) return;
    
    hotspotTable.innerHTML = `<tr><td colspan="5">⏳ Loading hotspot data...</td></tr>`;

    // Dynamically determine the correct API endpoint
    const apiUrl = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
        ? "http://127.0.0.1:5050/hotspot-prediction"
        : "/hotspot-prediction";

    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            hotspotTable.innerHTML = ""; // Clear previous entries

            if (!data || !data.hotspots || data.hotspots.length === 0) {
                hotspotTable.innerHTML = `<tr><td colspan="5">⚠️ No hotspots found.</td></tr>`;
                return;
            }

            data.hotspots.forEach(hotspot => {
                hotspotTable.insertAdjacentHTML("beforeend", `
                    <tr>
                        <td>${hotspot.city || "N/A"}</td>
                        <td>${hotspot.temperature !== undefined ? hotspot.temperature + "°C" : "N/A"}</td>
                        <td>${hotspot.humidity !== undefined ? hotspot.humidity + "%" : "N/A"}</td>
                        <td>${hotspot.wind_speed !== undefined ? hotspot.wind_speed + " m/s" : "N/A"}</td>
                        <td>${hotspot.risk_level || "Unknown"}</td>
                    </tr>
                `);
            });
        })
        .catch(error => {
            console.error("❌ Hotspot fetch error:", error);
            hotspotTable.innerHTML = `<tr><td colspan="5">⚠️ Failed to fetch hotspots: ${error.message}</td></tr>`;
        });
}

function getUserLocationForDisaster() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => fetchDisasterRisk(position.coords.latitude, position.coords.longitude),
            (error) => {
                alert("Error fetching location: " + error.message);
                setAllRiskIndicators("Error: " + error.message);
            }
        );
    } else {
        alert("Geolocation is not supported by your browser.");
        setAllRiskIndicators("Geolocation not supported");
    }
}

function fetchDisasterRisk(lat, lon) {
    // Update all status indicators to "Loading..."
    setAllRiskIndicators("Loading...");

    const apiUrl = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
        ? `http://127.0.0.1:5050/disaster-risk?lat=${lat}&lon=${lon}`
        : `/disaster-risk?lat=${lat}&lon=${lon}`;

    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                return response.json().then(errData => {
                    throw new Error(errData.error || "Failed to fetch disaster data");
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }

            // Update risk indicators with color coding
            updateRiskIndicator("floodRisk", data.flood_risk, "Flood");
            updateRiskIndicator("stormRisk", data.storm_risk, "Storm");
            updateRiskIndicator("earthquakeRisk", data.earthquake_risk, "Earthquake");
            updateRiskIndicator("wildfireRisk", data.wildfire_risk, "Wildfire");
        })
        .catch(error => {
            console.error("Disaster prediction error:", error);
            setAllRiskIndicators("Error");
            alert("Failed to get disaster risk: " + error.message);
        });
}

function setAllRiskIndicators(message) {
    const indicators = ["floodRisk", "stormRisk", "earthquakeRisk", "wildfireRisk"];
    indicators.forEach(id => {
        const element = document.getElementById(id);
        if (element) element.innerText = message;
    });
}

function updateRiskIndicator(elementId, riskValue, riskType) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const percentage = Math.round(riskValue * 100);
    
    let riskLevel = "";
    let color = "";
    
    if (riskValue < 0.3) {
        riskLevel = "Low";
        color = "green";
    } else if (riskValue < 0.6) {
        riskLevel = "Medium";
        color = "orange";
    } else {
        riskLevel = "High";
        color = "red";
    }
    
    element.innerHTML = `<span style="color: ${color}">${riskLevel} (${percentage}%)</span>`;
    element.title = `${riskType} risk based on current conditions and recent data`;
}

document.addEventListener("DOMContentLoaded", function() {
    const scanButton = document.getElementById('checkDisasterRisk');
    
    scanButton.addEventListener('click', function() {
        // Add active class for scanning animation
        this.classList.add('active');
        
        // Reset animation after it completes
        setTimeout(() => {
            this.classList.remove('active');
        }, 1500);
        
        // Get user location and fetch risks
        getUserLocationForDisaster();
    });
});