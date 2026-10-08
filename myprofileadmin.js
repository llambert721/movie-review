async function loadAdminProfile() {
    try {
        const response = await fetch("/api/me");

        if (!response.ok) {
            window.location.href = "login.html";
            return;
        }

        const user = await response.json();

        if (!user.is_admin && user.role !== "admin") {
            window.location.href = "myprofileuser.html";
            return;
        }

        const greeting = document.getElementById("adminGreeting");
        const username = document.getElementById("adminUsername");
        const displayName = document.getElementById("adminDisplayName");
        const role = document.getElementById("adminRole");

        if (greeting) greeting.textContent = user.display_name || user.username || user.name || "";
        if (username) username.textContent = user.username || user.name || "";
        if (displayName) displayName.textContent = user.display_name || user.name || user.username || "";
        if (role) role.textContent = "Administrator";

    } catch (error) {
        window.location.href = "login.html";
    }
}

document.getElementById("logoutButton").addEventListener("click", async () => {
    await fetch("/api/logout", { method: "POST" });
    window.location.href = "login.html";
});

loadAdminProfile();
