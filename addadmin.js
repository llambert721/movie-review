const form = document.getElementById("addAdminForm");
const message = document.getElementById("adminMessage");

async function verifyAdmin() {
    try {
        const response = await fetch("/api/me");
        if (!response.ok) {
            window.location.href = "login.html";
            return;
        }
        const user = await response.json();
        if (!user.is_admin && user.role !== "admin") {
            window.location.href = "myprofileuser.html";
        }
    } catch (err) {
        window.location.href = "login.html";
    }
}

document.getElementById("logoutButton").addEventListener("click", async () => {
    await fetch("/api/logout", { method: "POST" });
    window.location.href = "login.html";
});

form.addEventListener("submit", async event => {
    event.preventDefault();

    const username = document.getElementById("adminUsername").value.trim();
    const displayName = document.getElementById("adminDisplayName").value.trim();
    const password = document.getElementById("adminPassword").value;

    message.textContent = "";
    message.className = "message";

    try {
        const response = await fetch("/api/admin/create-admin", {
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
            message.textContent = data.error || "Failed to create administrator account.";
            message.className = "message error";
            return;
        }

        message.textContent = "Administrator account created successfully!";
        message.className = "message";
        message.style.color = "#2e7d32";

        form.reset();

    } catch (error) {
        message.textContent = "Unable to connect to the server.";
        message.className = "message error";
    }
});

verifyAdmin();
