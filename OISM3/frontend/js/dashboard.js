const token = localStorage.getItem("token");

if (!token) {

    window.location.href = "index.html";

}

const user =
    JSON.parse(localStorage.getItem("user"));

if (user) {

    document.getElementById("welcome").textContent =
        `Welcome, ${user.fullName}`;

}

function logout() {

    localStorage.removeItem("token");

    localStorage.removeItem("user");

    window.location.href = "index.html";
}

function goToProducts() {

    window.location.href = "products.html";

}

function goToInventory() {

    window.location.href = "inventory.html";

}

function goToOrders() {

    window.location.href = "orders.html";

}

function goToPOS() {

    window.location.href = "pos.html";

}