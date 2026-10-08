async function loadUserProfile() {
    try {
        const response = await fetch("/api/me");

        if (!response.ok) {
            window.location.href = "login.html";
            return;
        }

        const user = await response.json();

        const greeting = document.getElementById("userGreeting");
        const username = document.getElementById("userUsername");
        const displayName = document.getElementById("userDisplayName");
        const role = document.getElementById("userRole");
        const publicProfileLink = document.getElementById("publicProfileLink");

        const shownName = user.display_name || user.username || user.name || "";
        const rawUsername = user.username || user.email || "";

        if (greeting) greeting.textContent = shownName;
        if (username) username.textContent = rawUsername;
        if (displayName) displayName.textContent = shownName;
        if (role) role.textContent = user.is_admin || user.role === "admin" ? "Administrator" : "Member";
        if (publicProfileLink && rawUsername) {
            publicProfileLink.href = `userpage.html?username=${encodeURIComponent(rawUsername)}`;
        }

        await loadMyPosts();

    } catch (error) {
        window.location.href = "login.html";
    }
}

async function loadMyPosts() {
    const postsContainer = document.getElementById("postsList");
    const countElement = document.getElementById("postCount");

    try {
        const response = await fetch("/api/my/posts");

        if (!response.ok) {
            postsContainer.innerHTML = '<p class="muted">Unable to load reviews.</p>';
            return;
        }

        const posts = await response.json();

        if (countElement) {
            countElement.textContent = posts.length;
        }

        if (!posts || posts.length === 0) {
            postsContainer.innerHTML = '<p class="muted">You haven\'t posted any reviews yet. <a href="moviefeed.html">Browse movies</a> to write your first review!</p>';
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

    } catch (error) {
        postsContainer.innerHTML = '<p class="muted">Unable to load reviews.</p>';
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

document.getElementById("logoutButton").addEventListener("click", async () => {
    await fetch("/api/logout", { method: "POST" });
    window.location.href = "login.html";
});

loadUserProfile();
