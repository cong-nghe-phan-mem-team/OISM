document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
        const response = await fetch(`${window.location.origin}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const responseText = await response.text();

        let data = {};

        try {
            data = JSON.parse(responseText);
        } catch {
            data = {};
        }

        if (!response.ok) {
            throw new Error(
                data.detail || `Login failed (${response.status})`
            );
        }


        localStorage.setItem("token", data.access_token || data.token);
        if (data.user) {
            localStorage.setItem("user", JSON.stringify(data.user));
        }

        // LOGIN THÀNH CÔNG → CHUYỂN TRANG
        window.location.href = "dashboard.html";

    } catch (error) {
        console.error("LOGIN ERROR:", error);
        alert(error.message);
    }
});