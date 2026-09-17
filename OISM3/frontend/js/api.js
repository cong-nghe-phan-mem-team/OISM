const API_BASE_URL = window.location.origin;

async function apiRequest(url, options = {}) {

    const token = localStorage.getItem("token");

    const headers = {
        "Content-Type": "application/json",
        ...options.headers
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(
        API_BASE_URL + url,
        {
            ...options,
            headers: headers
        }
    );

    // Đọc response dưới dạng text trước
    const text = await response.text();

    let data;

    try {
        data = JSON.parse(text);
    } catch (error) {
        throw new Error(
            `API không trả về JSON (${response.status}). URL: ${API_BASE_URL + url}`
        );
    }

    if (!response.ok) {

    let errorMessage = "Something went wrong";

    if (data.detail) {

        if (typeof data.detail === "string") {
            errorMessage = data.detail;
        }

        else if (Array.isArray(data.detail)) {
            errorMessage = data.detail
                .map(error => {
                    if (typeof error === "object") {
                        return error.msg || JSON.stringify(error);
                    }
                    return error;
                })
                .join("\n");
        }

        else if (typeof data.detail === "object") {
            errorMessage =
                data.detail.msg ||
                JSON.stringify(data.detail);
        }
    }

    throw new Error(errorMessage);
}

    return data;
}


// ==== Kiểm tra đăng nhập ====
if (!localStorage.getItem("token")) {
    window.location.href = "index.html";
}


function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");

    window.location.href = "index.html";
}