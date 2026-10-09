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
            const postId = escapeHtml(post.id || "");
            const movieTitle = escapeHtml(post.movie_title || post.title || "Unknown Movie");
            const rating = escapeHtml(String(post.rating || 0));
            const comment = escapeHtml(post.comment || "");
            const date = post.created_at ? `<span class="review-date">${escapeHtml(post.created_at)}</span>` : "";

            return `
                <div class="review-item" data-post-id="${postId}">
                    <div class="review-view">
                        <div class="review-header">
                            <h3 class="review-title">${movieTitle}</h3>
                            <div>
                                <strong class="review-rating">Rating: ${rating}/10</strong>
                                ${date}
                            </div>
                        </div>
                        <p class="review-comment">${comment}</p>
                        <div class="review-actions">
                            <button type="button" class="btn-secondary edit-review-btn">Edit</button>
                            <button type="button" class="btn-danger delete-review-btn">Delete</button>
                        </div>
                    </div>
                    <form class="review-edit-form" hidden>
                        <label>Rating (1-10)
                            <input class="edit-rating" type="number" min="1" max="10" step="0.5" value="${rating}" required>
                        </label>
                        <label>Comment
                            <textarea class="edit-comment" rows="3" required>${comment}</textarea>
                        </label>
                        <div class="review-actions">
                            <button type="submit" class="primary">Save</button>
                            <button type="button" class="btn-secondary cancel-edit-btn">Cancel</button>
                        </div>
                        <p class="message edit-message"></p>
                    </form>
                </div>
            `;
        }).join("");

        bindReviewActions(postsContainer);

    } catch (error) {
        postsContainer.innerHTML = '<p class="muted">Unable to load reviews.</p>';
    }
}

function bindReviewActions(postsContainer) {
    postsContainer.querySelectorAll(".edit-review-btn").forEach(button => {
        button.addEventListener("click", () => {
            const item = button.closest(".review-item");
            item.querySelector(".review-view").hidden = true;
            item.querySelector(".review-edit-form").hidden = false;
        });
    });

    postsContainer.querySelectorAll(".cancel-edit-btn").forEach(button => {
        button.addEventListener("click", () => {
            const item = button.closest(".review-item");
            item.querySelector(".review-edit-form").hidden = true;
            item.querySelector(".review-view").hidden = false;
            const message = item.querySelector(".edit-message");
            if (message) message.textContent = "";
        });
    });

    postsContainer.querySelectorAll(".review-edit-form").forEach(form => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            const item = form.closest(".review-item");
            const postId = item.dataset.postId;
            const rating = form.querySelector(".edit-rating").value;
            const comment = form.querySelector(".edit-comment").value;
            const message = form.querySelector(".edit-message");

            try {
                const response = await fetch(`/api/posts/${encodeURIComponent(postId)}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ rating: Number(rating), comment })
                });
                const data = await response.json();

                if (!response.ok) {
                    message.textContent = data.error || "Failed to update review.";
                    return;
                }

                await loadMyPosts();
            } catch (error) {
                message.textContent = "Failed to update review.";
            }
        });
    });

    postsContainer.querySelectorAll(".delete-review-btn").forEach(button => {
        button.addEventListener("click", async () => {
            const item = button.closest(".review-item");
            const postId = item.dataset.postId;
            if (!confirm("Delete this review? This cannot be undone.")) {
                return;
            }

            try {
                const response = await fetch(`/api/posts/${encodeURIComponent(postId)}`, {
                    method: "DELETE"
                });
                const data = await response.json();

                if (!response.ok) {
                    alert(data.error || "Failed to delete review.");
                    return;
                }

                await loadMyPosts();
            } catch (error) {
                alert("Failed to delete review.");
            }
        });
    });
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
