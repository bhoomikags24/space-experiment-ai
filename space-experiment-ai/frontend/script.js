function startExperiment() {

    const experimentId =
        document.getElementById("experimentId").value;

    const participantId =
        document.getElementById("participantId").value;

    if (!experimentId || !participantId) {
        alert("Please enter all details");
        return;
    }

    alert("Experiment Started!");
}


function showStatus(result) {

    const status = document.getElementById("status");

    if (result.status === "CORRECT") {

        status.innerHTML =
            "🟢 Correct Sequence";

    } else {

        status.innerHTML =
            "🔴 WRONG SEQUENCE";
    }
}