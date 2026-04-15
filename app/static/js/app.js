document.addEventListener("DOMContentLoaded", () => {

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

                window.location.href = "/ui/profiles";

            } catch (error) {
                document.getElementById("login-error").innerText = "Something went wrong.";
            }
        });
    }

});