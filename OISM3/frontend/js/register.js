const form = document.getElementById("registerForm");
const result = document.getElementById("registerResult");

form.addEventListener("submit", async function (event) {

    event.preventDefault();

    const data = {
        tenantName: document.getElementById("tenantName").value.trim(),
        ownerEmail: document.getElementById("email").value.trim(),
        password: document.getElementById("password").value,
        fullName: document.getElementById("fullName").value.trim(),
        phone: document.getElementById("phone").value.trim() || null
    };

    try {

        const response = await fetch(
             "http://127.0.0.1:8000/auth/register", 
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(data)
            }
        );

        const responseText = await response.text();
         let resultData = {};

        try {
            resultData = JSON.parse(responseText);
        } catch {
            resultData = {};
        }

        if (!response.ok) {
            throw new Error(
                resultData.detail || `Register failed (${response.status})`
            );
        }

        result.className = "result-box success";
        result.textContent = resultData.message || "Register successfully!";

        form.reset();

    } catch (error) {
        console.error("REGISTER ERROR:", error);

        result.className = "result-box error";
        result.textContent = error.message;
    }
});