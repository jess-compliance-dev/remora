document.addEventListener("DOMContentLoaded", () => {

    // =========================
    // REGISTER
    // =========================
    const registerForm = document.getElementById("register-form");

    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const username = document.getElementById("username").value;
            const email = document.getElementById("email").value;
            const password = document.getElementById("password").value;

            try {
                const response = await fetch("/auth/register", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        username,
                        email,
                        password
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    document.getElementById("error-message").innerText = data.error;
                    return;
                }

                window.location.href = "/ui/check-email";

            } catch (error) {
                document.getElementById("error-message").innerText = "Something went wrong.";
            }
        });
    }

    // =========================
    // LOGIN
    // =========================
    const loginForm = document.getElementById("login-form");

    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const email = document.getElementById("login-email").value;
            const password = document.getElementById("login-password").value;

            try {
                const response = await fetch("/auth/login", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        email,
                        password
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    document.getElementById("login-error").innerText = data.error;
                    return;
                }

                localStorage.setItem("token", data.access_token);
                window.location.href = "/ui/dashboard";

            } catch (error) {
                document.getElementById("login-error").innerText = "Something went wrong.";
            }
        });
    }

    // =========================
    // CREATE PROFILE
    // =========================
    const createProfileForm = document.getElementById("create-profile-form");

    if (createProfileForm) {
        createProfileForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const token = localStorage.getItem("token");

            if (!token) {
                window.location.href = "/ui/login";
                return;
            }

            const payload = {
                full_name: document.getElementById("full_name").value,
                relationship: document.getElementById("relationship").value || null,
                birth_date: document.getElementById("birth_date").value || null,
                death_date: document.getElementById("death_date").value || null,
                status: document.getElementById("status").value,
                short_description: document.getElementById("short_description").value || null,
                profile_image_url: document.getElementById("profile_image_url").value || null
            };

            try {
                const response = await fetch("/profiles", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": "Bearer " + token
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (response.status === 401) {
                    localStorage.removeItem("token");
                    window.location.href = "/ui/login";
                    return;
                }

                if (!response.ok) {
                    document.getElementById("profile-error").innerText = data.error || "Unable to create profile.";
                    return;
                }

                window.location.href = "/ui/dashboard";

            } catch (error) {
                document.getElementById("profile-error").innerText = "Something went wrong.";
            }
        });
    }

});

async function loadProfiles(containerId) {
    const token = localStorage.getItem("token");
    const container = document.getElementById(containerId);

    if (!container) return;

    if (!token) {
        window.location.href = "/ui/login";
        return;
    }

    try {
        const response = await fetch("/profiles", {
            method: "GET",
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (response.status === 401) {
            localStorage.removeItem("token");
            window.location.href = "/ui/login";
            return;
        }

        const data = await response.json();

        if (!Array.isArray(data) || data.length === 0) {
            container.innerHTML = `
                <div class="phone-card">
                    <p>No profiles yet.</p>
                    <p class="muted">Create your first memorial profile to get started.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = data.map(profile => `
            <a href="/ui/profiles" class="profile-card">
                <div class="avatar large"></div>
                <div class="profile-text">
                    <h3>${profile.full_name}</h3>
                    <p class="muted">${profile.relationship || ""}</p>
                    <span class="pill">${profile.status}</span>
                </div>
            </a>
        `).join("");

    } catch (error) {
        container.innerHTML = `<p style="color:red;">Could not load profiles.</p>`;
    }
}

function logout() {
    localStorage.removeItem("token");
    window.location.href = "/ui/login";
}
