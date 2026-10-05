async function loadCurrentUser() {
    const response = await fetch("/api/me");

    if (!response.ok) {
        window.location.href = "/";
        return;
    }

    const user = await response.json();

    const name = document.getElementById("userName");
    const email = document.getElementById("userEmail");
    const role = document.getElementById("userRole");

    if (name) name.textContent = user.name;
    if (email) email.textContent = user.email;
    if (role) role.textContent = user.role;
}

document.getElementById("logoutButton").addEventListener("click", async () => {
    await fetch("/api/logout", {method: "POST"});
    window.location.href = "/";
});

loadCurrentUser();
