let currentUser = null;

async function initMovieFeedPage() {
    const authButton = document.getElementById("authButton");
    const myProfileLink = document.getElementById("myProfileLink");
    const topbar = document.querySelector(".topbar");
    const addSection = document.getElementById("addMovieSection");

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
                addSection.hidden = false;
                bindAddMovieForm();
            } else {
                myProfileLink.href = "myprofileuser.html";
                addSection.hidden = true;
            }
        } else {
            authButton.textContent = "Login";
            authButton.onclick = () => { window.location.href = "login.html"; };
            if (myProfileLink) myProfileLink.hidden = true;
            addSection.hidden = true;
        }
    } catch (error) {
        authButton.textContent = "Login";
        authButton.onclick = () => { window.location.href = "login.html"; };
        if (myProfileLink) myProfileLink.hidden = true;
        addSection.hidden = true;
    }

    ["sortSelect", "orderSelect", "genreSelect"].forEach(id => {
        document.getElementById(id).addEventListener("change", loadMovies);
    });

    await loadGenres();
    await loadMovies();
}

async function loadGenres() {
    const select = document.getElementById("genreSelect");
    const selected = select.value;
    try {
        const response = await fetch("/api/genres");
        const genres = await response.json();
        select.innerHTML = '<option value="">All genres</option>' + genres.map(g =>
            `<option value="${escapeHtml(g)}">${escapeHtml(g)}</option>`
        ).join("");
        select.value = genres.includes(selected) ? selected : "";
    } catch (error) {
        // keep the existing options
    }
}

async function loadMovies() {
    const list = document.getElementById("movieList");
    const params = new URLSearchParams({
        sort: document.getElementById("sortSelect").value,
        order: document.getElementById("orderSelect").value
    });
    const genre = document.getElementById("genreSelect").value;
    if (genre) params.set("genre", genre);

    try {
        const response = await fetch(`/api/movies?${params}`);
        if (!response.ok) {
            list.innerHTML = '<p class="muted">Unable to load movies.</p>';
            return;
        }
        const movies = await response.json();
        if (!movies.length) {
            list.innerHTML = '<p class="muted">No movies found.</p>';
            return;
        }
        list.innerHTML = movies.map(renderMovieCard).join("");
        bindMovieActions(list);
    } catch (error) {
        list.innerHTML = '<p class="muted">Unable to load movies.</p>';
    }
}

function formatRating(value) {
    if (value === null || value === undefined) return "No ratings yet";
    return `${Number(value).toFixed(1)}/10`;
}

function renderMovieCard(movie) {
    const isAdmin = currentUser && (currentUser.is_admin || currentUser.role === "admin");
    const id = escapeHtml(movie.id);
    const reviews = `${movie.review_count} review${movie.review_count === 1 ? "" : "s"}`;

    return `
    <article class="movie-card" data-movie-id="${id}">
        <div class="movie-view">
            <h3><a href="moviepage.html?id=${encodeURIComponent(movie.id)}">${escapeHtml(movie.title)}</a></h3>
            <div class="movie-meta">
                <span class="genre-tag">${escapeHtml(movie.genre)}</span>
                <span>${escapeHtml(movie.release_date)}</span>
                <span class="avg-rating">${escapeHtml(formatRating(movie.avg_rating))}</span>
                <span>${reviews}</span>
            </div>
            <p class="movie-description">${escapeHtml(movie.description)}</p>
            ${isAdmin ? `
            <div class="review-actions">
                <button type="button" class="btn-secondary edit-movie-btn">Edit</button>
                <button type="button" class="btn-danger delete-movie-btn">Delete</button>
            </div>` : ""}
        </div>
        ${isAdmin ? `
        <form class="movie-edit-form" hidden>
            <label>Title <input class="edit-title" type="text" value="${escapeHtml(movie.title)}" required></label>
            <label>Release date <input class="edit-date" type="date" value="${escapeHtml(movie.release_date)}" required></label>
            <label>Genre <input class="edit-genre" type="text" value="${escapeHtml(movie.genre)}" required></label>
            <label>Description <textarea class="edit-description" rows="3" required>${escapeHtml(movie.description)}</textarea></label>
            <div class="review-actions">
                <button type="submit" class="primary">Save changes</button>
                <button type="button" class="btn-secondary cancel-edit-btn">Cancel</button>
            </div>
            <p class="message edit-message"></p>
        </form>` : ""}
    </article>`;
}

function bindMovieActions(list) {
    list.querySelectorAll(".edit-movie-btn").forEach(button => {
        button.addEventListener("click", () => {
            const card = button.closest(".movie-card");
            card.querySelector(".movie-view").hidden = true;
            card.querySelector(".movie-edit-form").hidden = false;
        });
    });

    list.querySelectorAll(".cancel-edit-btn").forEach(button => {
        button.addEventListener("click", () => {
            const card = button.closest(".movie-card");
            card.querySelector(".movie-edit-form").hidden = true;
            card.querySelector(".movie-view").hidden = false;
            const message = card.querySelector(".edit-message");
            if (message) message.textContent = "";
        });
    });

    list.querySelectorAll(".movie-edit-form").forEach(form => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            const card = form.closest(".movie-card");
            const message = form.querySelector(".edit-message");
            try {
                const response = await fetch(`/api/movies/${encodeURIComponent(card.dataset.movieId)}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        title: form.querySelector(".edit-title").value,
                        release_date: form.querySelector(".edit-date").value,
                        genre: form.querySelector(".edit-genre").value,
                        description: form.querySelector(".edit-description").value
                    })
                });
                const data = await response.json();
                if (!response.ok) {
                    message.textContent = data.error || "Failed to update movie.";
                    return;
                }
                await loadGenres();
                await loadMovies();
            } catch (error) {
                message.textContent = "Failed to update movie.";
            }
        });
    });

    list.querySelectorAll(".delete-movie-btn").forEach(button => {
        button.addEventListener("click", async () => {
            const card = button.closest(".movie-card");
            const title = card.querySelector("h3").textContent;
            if (!confirm(`Delete "${title}" and all of its reviews? This cannot be undone.`)) {
                return;
            }
            try {
                const response = await fetch(`/api/movies/${encodeURIComponent(card.dataset.movieId)}`, {
                    method: "DELETE"
                });
                const data = await response.json();
                if (!response.ok) {
                    alert(data.error || "Failed to delete movie.");
                    return;
                }
                await loadGenres();
                await loadMovies();
            } catch (error) {
                alert("Failed to delete movie.");
            }
        });
    });
}

function bindAddMovieForm() {
    const form = document.getElementById("addMovieForm");
    const message = document.getElementById("addMessage");
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        message.textContent = "";
        message.className = "message";
        try {
            const response = await fetch("/api/movies", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    title: document.getElementById("newTitle").value,
                    release_date: document.getElementById("newDate").value,
                    genre: document.getElementById("newGenre").value,
                    description: document.getElementById("newDescription").value
                })
            });
            const data = await response.json();
            if (!response.ok) {
                message.textContent = data.error || "Failed to add movie.";
                return;
            }
            form.reset();
            message.textContent = "Movie added.";
            message.className = "message success";
            await loadGenres();
            await loadMovies();
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

initMovieFeedPage();
