const form = document.getElementById("addUserForm");
const message = document.getElementById("message");

form.addEventListener("submit", async event => {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const displayName = document.getElementById("displayName").value.trim();
    const password = document.getElementById("password").value;

    message.textContent = "";
    message.className = "message";

    try {
        const response = await fetch("/api/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: username,
                display_name: displayName,
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            message.textContent = data.error || "Failed to create account.";
            message.className = "message error";
            return;
        }

        message.textContent = "Account created successfully! Redirecting to login...";
        message.className = "message";
        message.style.color = "#2e7d32";

        setTimeout(() => {
            window.location.href = "login.html";
        }, 1500);

    } catch (error) {
        message.textContent = "Unable to connect to the server.";
        message.className = "message error";
    }
});
