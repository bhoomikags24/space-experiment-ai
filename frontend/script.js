const API_URL = "https://space-experiment-ai.onrender.com";

async function loadExperiment() {
    try {
        const response = await fetch(`${API_URL}/experiment`);

        if (!response.ok) {
            throw new Error("Backend response error");
        }

        const data = await response.json();

        updateDashboard(data);

    } catch (error) {
        console.error("Backend connection error:", error);

        const statusElement = document.getElementById("connectionStatus");

        if (statusElement) {
            statusElement.textContent = "Cannot connect to backend";
        }
    }
}

function updateDashboard(data) {

    const experimentId = document.getElementById("experimentId");
    const participantId = document.getElementById("participantId");
    const currentActivity = document.getElementById("currentActivity");
    const currentStep = document.getElementById("currentStep");
    const status = document.getElementById("status");
    const confidence = document.getElementById("confidence");
    const expectedActivity = document.getElementById("expectedActivity");

    if (experimentId) {
        experimentId.textContent = data.experiment_id || "EXP001";
    }

    if (participantId) {
        participantId.textContent = data.participant_id || "P001";
    }

    if (currentActivity) {
        currentActivity.textContent = data.current_activity || "-";
    }

    if (currentStep) {
        currentStep.textContent =
            `${data.current_step || 1}/${data.total_steps || 5}`;
    }

    if (status) {
        status.textContent = data.status || "WAITING";
    }

    if (confidence) {
        confidence.textContent =
            `${((data.confidence || 0) * 100).toFixed(1)}%`;
    }

    if (expectedActivity) {
        expectedActivity.textContent =
            data.expected_activity || "-";
    }
}

async function loadLogs() {
    try {
        const response = await fetch(`${API_URL}/logs`);

        if (!response.ok) {
            throw new Error("Could not load logs");
        }

        const data = await response.json();

        displayLogs(data.logs || []);

    } catch (error) {
        console.error("Log loading error:", error);
    }
}

function displayLogs(logs) {

    const tableBody = document.getElementById("activityLog");

    if (!tableBody) {
        return;
    }

    tableBody.innerHTML = "";

    logs.forEach(log => {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${log.time || "-"}</td>
            <td>${log.step || "-"}</td>
            <td>${log.activity || "-"}</td>
            <td>${log.status || "-"}</td>
            <td>${((log.confidence || 0) * 100).toFixed(1)}%</td>
        `;

        tableBody.appendChild(row);
    });
}

async function checkBackend() {

    try {

        const response = await fetch(`${API_URL}/status`);

        if (!response.ok) {
            throw new Error("Backend unavailable");
        }

        const data = await response.json();

        const connectionStatus =
            document.getElementById("connectionStatus");

        if (connectionStatus) {
            connectionStatus.textContent =
                data.status || "Backend connected successfully";
        }

    } catch (error) {

        const connectionStatus =
            document.getElementById("connectionStatus");

        if (connectionStatus) {
            connectionStatus.textContent =
                "Cannot connect to backend";
        }
    }
}

async function refreshDashboard() {
    await checkBackend();
    await loadExperiment();
    await loadLogs();
}

refreshDashboard();

setInterval(refreshDashboard, 2000);
