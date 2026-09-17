if (!localStorage.getItem("token")) {
    window.location.href = "index.html";
}

function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "index.html";
}

let posItemCount = 0;
let retailPriceBySku = new Map();

async function loadRetailPrices() {
    try {
        const result = await apiRequest("/products", { method: "GET" });
        (result.data || []).forEach(product => {
            (product.variants || []).forEach(variant => {
                retailPriceBySku.set(String(variant.sku).toLowerCase(), Number(variant.retailPrice || 0));
            });
        });
    } catch (err) {
        console.warn("Cannot preload product prices:", err.message);
    }
}

function addPosItemRow() {
    posItemCount++;
    const id = posItemCount;
    const container = document.getElementById("posItemsContainer");
    const row = document.createElement("div");
    row.className = "variant-row";
    row.id = "pos-item-row-" + id;
    row.innerHTML = `
        <div class="form-field">
            <label>SKU</label>
            <input type="text" class="pos-sku" placeholder="SKU-001">
        </div>
        <div class="form-field">
            <label>Số lượng</label>
            <input type="number" class="pos-qty" placeholder="1" min="1">
        </div>
        <div class="form-field">
            <label>Đơn giá (lấy từ ProductVariant)</label>
            <input type="number" class="pos-price" placeholder="100000" min="0" readonly>
        </div>
        <button type="button" class="danger" onclick="removePosItemRow(${id})">X</button>
    `;
    container.appendChild(row);

    row.querySelector(".pos-sku").addEventListener("input", function () {
        const price = retailPriceBySku.get(this.value.trim().toLowerCase());
        row.querySelector(".pos-price").value = price ?? "";
    });
}

function removePosItemRow(id) {
    const row = document.getElementById("pos-item-row-" + id);
    if (row) row.remove();
}

async function initPOS() {
    await loadRetailPrices();
    addPosItemRow();
}

document.getElementById("checkoutForm").addEventListener("submit", async function (event) {
    event.preventDefault();
    const resultBox = document.getElementById("checkoutResult");
    const items = [];

    document.querySelectorAll("#posItemsContainer .variant-row").forEach(function (row) {
        const sku = row.querySelector(".pos-sku").value.trim();
        const quantity = parseInt(row.querySelector(".pos-qty").value, 10);
        if (sku) {
            items.push({
                sku,
                quantity: Number.isInteger(quantity) ? quantity : 0,
                price: row.querySelector(".pos-price").value ? Number(row.querySelector(".pos-price").value) : null
            });
        }
    });

    const payload = {
        items,
        discount: Number(document.getElementById("discount").value || 0),
        payment_method: document.getElementById("paymentMethod").value
    };

    try {
        const result = await apiRequest("/pos/checkout", {
            method: "POST",
            body: JSON.stringify(payload)
        });
        resultBox.classList.remove("empty");
        resultBox.textContent = JSON.stringify(result, null, 2);
        await loadRetailPrices();
    } catch (err) {
        resultBox.classList.remove("empty");
        resultBox.textContent = "Lỗi: " + err.message;
    }
});

initPOS();
