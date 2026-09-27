const API_URL = "https://space-experiment-ai.onrender.com";

async function refreshDashboard() {
    try {
        const statusResponse = await fetch(`${API_URL}/status`);
        const statusData = await statusResponse.json();

        const connectionStatus = document.getElementById("connectionStatus");
        if (connectionStatus) {
            connectionStatus.textContent =
                statusData.status || "Backend connected successfully";
        }

        const experimentResponse = await fetch(`${API_URL}/experiment`);
        const data = await experimentResponse.json();

        setText("experimentId", data.experiment_id || "EXP001");
        setText("participantId", data.participant_id || "P001");
        setText("currentActivity", data.current_activity || "-");
        setText(
            "currentStep",
            `${data.current_step || 1}/${data.total_steps || 5}`
        );
        setText("status", data.status || "WAITING");
        setText(
            "confidence",
            `${((data.confidence || 0) * 100).toFixed(1)}%`
        );
        setText("expectedActivity", data.expected_activity || "-");

    } catch (error) {
        console.error(error);

        const connectionStatus =
            document.getElementById("connectionStatus");

        if (connectionStatus) {
            connectionStatus.textContent = "Cannot connect to backend";
        }
    }
}

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

refreshDashboard();
setInterval(refreshDashboard, 3000);
