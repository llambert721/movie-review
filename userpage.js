async function initUserPage() {
    const params = new URLSearchParams(window.location.search);
    let targetUser = params.get("username") || params.get("id");

    const authButton = document.getElementById("authButton");
    const myProfileLink = document.getElementById("myProfileLink");

    let currentUser = null;
    try {
        const meRes = await fetch("/api/me");
        if (meRes.ok) {
            currentUser = await meRes.json();
            authButton.textContent = "Logout";
            authButton.onclick = async () => {
                await fetch("/api/logout", { method: "POST" });
                window.location.href = "login.html";
            };
            if (currentUser.is_admin || currentUser.role === "admin") {
                myProfileLink.href = "myprofileadmin.html";
            } else {
                myProfileLink.href = "myprofileuser.html";
            }
        } else {
            authButton.textContent = "Login";
            authButton.onclick = () => {
                window.location.href = "login.html";
            };
            if (myProfileLink) myProfileLink.style.display = "none";
        }
    } catch (e) {
        authButton.textContent = "Login";
        authButton.onclick = () => {
            window.location.href = "login.html";
        };
        if (myProfileLink) myProfileLink.style.display = "none";
    }

    if (!targetUser && currentUser) {
        targetUser = currentUser.username || currentUser.email;
    }

    if (!targetUser) {
        document.getElementById("profileDisplayName").textContent = "User Not Found";
        document.getElementById("profileUsername").textContent = "none";
        document.getElementById("userPostsList").innerHTML = '<p class="muted">No user specified. Please return to the <a href="feed.html">feed</a>.</p>';
        return;
    }

    await loadUserData(targetUser);
}

async function loadUserData(targetUser) {
    const displayName = document.getElementById("profileDisplayName");
    const username = document.getElementById("profileUsername");
    const infoUsername = document.getElementById("infoUsername");
    const infoDisplayName = document.getElementById("infoDisplayName");
    const infoRole = document.getElementById("infoRole");
    const headerName = document.getElementById("reviewsHeaderName");
    const postCountElement = document.getElementById("userPostCount");
    const postsContainer = document.getElementById("userPostsList");

    try {
        const userRes = await fetch(`/api/users/${encodeURIComponent(targetUser)}`);
        if (!userRes.ok) {
            displayName.textContent = "User Not Found";
            username.textContent = targetUser;
            postsContainer.innerHTML = '<p class="muted">Could not find user profile.</p>';
            return;
        }

        const user = await userRes.json();
        const shownName = user.display_name || user.username || user.name || "";
        const rawUsername = user.username || user.email || targetUser;

        displayName.textContent = shownName;
        username.textContent = rawUsername;
        infoUsername.textContent = rawUsername;
        infoDisplayName.textContent = shownName;
        infoRole.textContent = user.is_admin || user.role === "admin" ? "Administrator" : "Member";
        headerName.textContent = shownName;

        const postsRes = await fetch(`/api/users/${encodeURIComponent(targetUser)}/posts`);
        if (!postsRes.ok) {
            postsContainer.innerHTML = '<p class="muted">Unable to load reviews.</p>';
            return;
        }

        const posts = await postsRes.json();
        if (postCountElement) {
            postCountElement.textContent = posts.length;
        }

        if (!posts || posts.length === 0) {
            postsContainer.innerHTML = '<p class="muted">This user has not posted any reviews yet.</p>';
            return;
        }

        postsContainer.innerHTML = posts.map(post => {
            const movieTitle = escapeHtml(post.movie_title || post.title || "Unknown Movie");
            const rating = escapeHtml(String(post.rating || 0));
            const comment = escapeHtml(post.comment || "");
            const date = post.created_at ? `<span class="review-date">${escapeHtml(post.created_at)}</span>` : "";

            return `
                <div class="review-item">
                    <div class="review-header">
                        <h3 class="review-title">${movieTitle}</h3>
                        <div>
                            <strong class="review-rating">Rating: ${rating}/10</strong>
                            ${date}
                        </div>
                    </div>
                    <p class="review-comment">${comment}</p>
                </div>
            `;
        }).join("");

    } catch (err) {
        postsContainer.innerHTML = '<p class="muted">Error loading user profile.</p>';
    }
}

function escapeHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

initUserPage();
