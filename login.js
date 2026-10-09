const form = document.getElementById("loginForm");
const message = document.getElementById("message");

form.addEventListener("submit", async event => {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    message.textContent = "";
    message.className = "message";

    try {
        const response = await fetch("/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            message.textContent = data.error || "Login failed.";
            message.className = "message error";
            return;
        }

        if (data.is_admin || data.role === "admin") {
            window.location.href = "myprofileadmin.html";
        } else {
            window.location.href = "myprofileuser.html";
        }

    } catch (error) {
        message.textContent = "Unable to connect to the server.";
        message.className = "message error";
    }
});