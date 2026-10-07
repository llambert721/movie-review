const form = document.getElementById("loginForm");
const message = document.getElementById("message");

/*
TODO 1 - FRONTEND LOGIN

When the form is submitted:
1. Prevent page reload.
2. Read email and password.
3. Create an object.
4. POST JSON to /api/login.
5. Convert the response to JSON.
6. If login fails, show the error.
7. If role is "admin", go to /admin.
8. If role is "user", go to /user.
*/

form.addEventListener("submit", async event => {
    event.preventDefault();

    const email = document.getElementById("email").value.trim();
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
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            message.textContent = data.error || "Login failed.";
            message.className = "message error";
            return;
        }

        if (data.role === "admin") {
            window.location.href = "/admin";
        } else if (data.role === "user") {
            window.location.href = "/user";
        } else {
            message.textContent = "Unknown account role.";
            message.className = "message error";
        }

    } catch (error) {
        message.textContent = "Unable to connect to the server.";
        message.className = "message error";
    }
});