const movieId = new URLSearchParams(window.location.search).get("id");
let currentUser = null;

async function initMoviePage() {
    const authButton = document.getElementById("authButton");
    const myProfileLink = document.getElementById("myProfileLink");
    const topbar = document.querySelector(".topbar");
    const reviewFormSection = document.getElementById("reviewFormSection");
    const guestSection = document.getElementById("guestPromptSection");

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
                if (topbar) topbar.classList.add("adminbar");
            } else {
                myProfileLink.href = "myprofileuser.html";
            }
        } else {
            authButton.textContent = "Login";
            authButton.onclick = () => { window.location.href = "login.html"; };
            if (myProfileLink) myProfileLink.hidden = true;
        }
    } catch (error) {
        authButton.textContent = "Login";
        authButton.onclick = () => { window.location.href = "login.html"; };
        if (myProfileLink) myProfileLink.hidden = true;
    }

    const found = await loadMovie();
    if (!found) {
        reviewFormSection.hidden = true;
        guestSection.hidden = true;
        return;
    }

    if (currentUser) {
        reviewFormSection.hidden = false;
        guestSection.hidden = true;
        bindPostForm();
    } else {
        reviewFormSection.hidden = true;
        guestSection.hidden = false;
    }

    await loadReviews();
}

function formatRating(value) {
    if (value === null || value === undefined) return "No ratings yet";
    return `${Number(value).toFixed(1)}/10`;
}

async function loadMovie() {
    if (!movieId) {
        document.getElementById("movieTitle").textContent = "No movie selected";
        document.getElementById("reviewList").innerHTML = '<p class="muted">Pick a movie from the <a href="moviefeed.html">movie list</a>.</p>';
        return false;
    }

    try {
        const response = await fetch(`/api/movies/${encodeURIComponent(movieId)}`);
        if (!response.ok) {
            document.getElementById("movieTitle").textContent = "Movie not found";
            document.getElementById("reviewList").innerHTML = '<p class="muted">This movie may have been removed. Return to the <a href="moviefeed.html">movie list</a>.</p>';
            return false;
        }
        const movie = await response.json();
        document.title = `${movie.title} - Movie Review`;
        document.getElementById("movieTitle").textContent = movie.title;
        document.getElementById("movieGenre").textContent = movie.genre;
        document.getElementById("movieDate").textContent = movie.release_date;
        document.getElementById("movieRating").textContent = formatRating(movie.avg_rating);
        document.getElementById("movieCount").textContent = `${movie.review_count} review${movie.review_count === 1 ? "" : "s"}`;
        document.getElementById("movieDescription").textContent = movie.description;
        return true;
    } catch (error) {
        document.getElementById("movieTitle").textContent = "Unable to load movie";
        return false;
    }
}

async function loadReviews() {
    const list = document.getElementById("reviewList");
    try {
        const response = await fetch(`/api/movies/${encodeURIComponent(movieId)}/posts`);
        if (!response.ok) {
            list.innerHTML = '<p class="muted">Unable to load reviews.</p>';
            return;
        }
        const posts = await response.json();
        if (!posts.length) {
            list.innerHTML = '<p class="muted">No reviews yet. Be the first to post one.</p>';
            return;
        }

        list.innerHTML = posts.map(post => {
            const postId = escapeHtml(post.id || "");
            const rating = escapeHtml(String(post.rating || 0));
            const comment = escapeHtml(post.comment || "");
            const date = post.created_at ? `<span class="review-date">${escapeHtml(post.created_at)}</span>` : "";
            const authorName = escapeHtml(post.display_name || "Unknown User");
            const authorUser = post.username || "";
            const byline = authorUser
                ? `<p class="feed-byline"><a href="userpage.html?username=${encodeURIComponent(authorUser)}">${authorName}</a> <span>@${escapeHtml(authorUser)}</span></p>`
                : `<p class="feed-byline">${authorName}</p>`;

            const isOwner = currentUser && String(currentUser.user_id) === String(post.user_id);
            const isAdmin = currentUser && (currentUser.is_admin || currentUser.role === "admin");
            let actions = "";
            if (isOwner) {
                actions = `
                    <div class="review-actions">
                        <button type="button" class="btn-secondary edit-review-btn">Edit</button>
                        <button type="button" class="btn-danger delete-review-btn">Delete</button>
                    </div>`;
            } else if (isAdmin) {
                actions = `
                    <div class="review-actions">
                        <button type="button" class="btn-danger delete-review-btn">Delete</button>
                    </div>`;
            }

            const editForm = isOwner ? `
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
                </form>` : "";

            return `
                <div class="review-item feed-item" data-post-id="${postId}">
                    <div class="review-view">
                        ${byline}
                        <div class="review-header">
                            <h3 class="review-title">Review</h3>
                            <div>
                                <strong class="review-rating">Rating: ${rating}/10</strong>
                                ${date}
                            </div>
                        </div>
                        <p class="review-comment">${comment}</p>
                        ${actions}
                    </div>
                    ${editForm}
                </div>
            `;
        }).join("");

        bindReviewActions(list);
    } catch (error) {
        list.innerHTML = '<p class="muted">Unable to load reviews.</p>';
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
                await loadMovie();
                await loadReviews();
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
                await loadMovie();
                await loadReviews();
            } catch (error) {
                alert("Failed to delete review.");
            }
        });
    });
}

function bindPostForm() {
    const form = document.getElementById("postForm");
    const message = document.getElementById("postMessage");
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        message.textContent = "";
        message.className = "message";
        try {
            const response = await fetch("/api/posts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    movie_id: movieId,
                    rating: Number(document.getElementById("rating").value),
                    comment: document.getElementById("comment").value
                })
            });
            const data = await response.json();
            if (!response.ok) {
                message.textContent = data.error || "Failed to post review.";
                return;
            }
            form.reset();
            message.textContent = "Review posted.";
            message.className = "message success";
            await loadMovie();
            await loadReviews();
        } catch (error) {
            message.textContent = "Unable to connect to the server.";
        }
    });
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

initMoviePage();
