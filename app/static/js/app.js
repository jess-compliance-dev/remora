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
                    document.getElementById("error-message").innerText = data.error || "Registration failed.";
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
                    document.getElementById("login-error").innerText = data.error || "Login failed.";
                    return;
                }

                // 🔐 Token speichern
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

            let uploadedImageUrl = null;
            const imageFile = document.getElementById("profile-image-input")?.files[0];

            try {
                // 🔥 Upload Bild zuerst
                if (imageFile) {
                    const formData = new FormData();
                    formData.append("image", imageFile);

                    const uploadResponse = await fetch("/profiles/upload-image", {
                        method: "POST",
                        headers: {
                            "Authorization": "Bearer " + token
                        },
                        body: formData
                    });

                    const uploadData = await uploadResponse.json();

                    if (!uploadResponse.ok) {
                        document.getElementById("profile-error").innerText =
                            uploadData.error || "Image upload failed.";
                        return;
                    }

                    uploadedImageUrl = uploadData.profile_image_url;
                }

                // 🔥 Profil erstellen
                const payload = {
                    full_name: document.getElementById("full_name").value,
                    relationship: document.getElementById("relationship").value || null,
                    birth_date: document.getElementById("birth_date")?.value || null,
                    death_date: document.getElementById("death_date")?.value || null,
                    short_description: document.getElementById("short_description").value || null,
                    profile_image_url: uploadedImageUrl
                };

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
                    document.getElementById("profile-error").innerText =
                        data.error || "Could not create profile.";
                    return;
                }

                window.location.href = "/ui/dashboard";

            } catch (error) {
                document.getElementById("profile-error").innerText = "Something went wrong.";
            }
        });
    }

});


// =========================
// LOAD PROFILES
// =========================
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
                <div class="empty-state-card">
                    <h3>No memories yet</h3>
                    <p class="muted">Create your first memorial profile to begin capturing moments.</p>
                    <a href="/ui/profiles/create" class="btn btn-primary small" style="margin-top:12px;">Create profile</a>
                </div>
            `;
            return;
        }

        container.innerHTML = data.map(profile => `
            <a href="/ui/profiles/${profile.profile_id}" class="profile-row-card">
                <div class="avatar large">
                    ${profile.profile_image_url
                        ? `<img src="${profile.profile_image_url}" />`
                        : ""
                    }
                </div>
                <div class="profile-row-text">
                    <h3>${profile.full_name}</h3>
                    <p class="muted">${profile.relationship || ""}</p>
                    <span class="pill">${buildLifeStatus(profile.birth_date, profile.death_date)}</span>
                </div>
            </a>
        `).join("");

    } catch (error) {
        container.innerHTML = `<p style="color:red;">Failed to load profiles.</p>`;
    }
}


// =========================
// HELPER: LIFE STATUS
// =========================
function buildLifeStatus(birthDate, deathDate) {
    if (deathDate) return "Remembered";
    if (birthDate) return "Living story";
    return "Profile";
}


// =========================
// LOGOUT
// =========================
function logout() {
    localStorage.removeItem("token");
    window.location.href = "/ui/login";
}
