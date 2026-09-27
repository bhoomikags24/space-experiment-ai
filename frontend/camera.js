

async function startCamera() {

    const video = document.getElementById("camera");

    const stream = await navigator.mediaDevices.getUserMedia({
        video: true
    });

    video.srcObject = stream;
}


async function checkBackend() {

    const status = document.getElementById("status");

    try {
        const response = await fetch("http://127.0.0.1:8000/status");

        const data = await response.json();

        status.innerHTML = "🟢 " + data.status;

    } catch (error) {

        status.innerHTML = "🔴 Backend connection failed";

        console.error(error);
    }
}
