if (!localStorage.getItem("token")) {
    window.location.href = "index.html";
}

function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "index.html";
}

let itemCount = 0;
let retailPriceBySku = new Map();

async function loadRetailPrices() {
    try {
        const result = await apiRequest("/products", { method: "GET" });
        (result.data || []).forEach(product => {
            (product.variants || []).forEach(variant => {
                retailPriceBySku.set(String(variant.sku).toLowerCase(), Number(variant.retailPrice || 0));
                retailPriceBySku.set(String(variant.id), Number(variant.retailPrice || 0));
            });
        });
    } catch (err) {
        console.warn("Cannot preload product prices:", err.message);
    }
}

function addOrderItemRow() {
    itemCount++;
    const id = itemCount;
    const container = document.getElementById("orderItemsContainer");
    const row = document.createElement("div");
    row.className = "variant-row";
    row.id = "order-item-row-" + id;
    row.innerHTML = `
        <div class="form-field">
            <label>SKU ID</label>
            <input type="text" class="item-sku" placeholder="SKU-001">
        </div>
        <div class="form-field">
            <label>Số lượng</label>
            <input type="number" class="item-qty" placeholder="2" min="1">
        </div>
        <div class="form-field">
            <label>Đơn giá (lấy từ ProductVariant)</label>
            <input type="number" class="item-price" placeholder="100000" min="0" readonly>
        </div>
        <button type="button" class="danger" onclick="removeOrderItemRow(${id})">X</button>
    `;
    container.appendChild(row);
    row.querySelector(".item-sku").addEventListener("input", function () {
        const price = retailPriceBySku.get(this.value.trim().toLowerCase()) ?? retailPriceBySku.get(this.value.trim());
        row.querySelector(".item-price").value = price ?? "";
    });
}

function removeOrderItemRow(id) {
    const row = document.getElementById("order-item-row-" + id);
    if (row) row.remove();
}

async function initOrders() {
    await loadRetailPrices();
    addOrderItemRow();
}

document.getElementById("createOrderForm").addEventListener("submit", async function (event) {
    event.preventDefault();
    const resultBox = document.getElementById("createOrderResult");
    const items = [];

    document.querySelectorAll("#orderItemsContainer .variant-row").forEach(function (row) {
        const sku_id = row.querySelector(".item-sku").value.trim();
        const quantity = parseInt(row.querySelector(".item-qty").value, 10);
        if (sku_id) {
            items.push({
                sku_id,
                quantity: Number.isInteger(quantity) ? quantity : 0,
                unit_price: row.querySelector(".item-price").value ? Number(row.querySelector(".item-price").value) : null
            });
        }
    });

    const payload = {
        branch_id: document.getElementById("branchId").value,
        sales_channel: document.getElementById("salesChannel").value,
        items
    };

    try {
        const result = await apiRequest("/orders", {
            method: "POST",
            body: JSON.stringify(payload)
        });
        resultBox.classList.remove("empty");
        resultBox.textContent = JSON.stringify(result, null, 2);
        if (result.order_id) document.getElementById("actionOrderId").value = result.order_id;
    } catch (err) {
        resultBox.classList.remove("empty");
        resultBox.textContent = "Lỗi: " + err.message;
    }
});

document.getElementById("orderActionForm").addEventListener("submit", async function (event) {
    event.preventDefault();
    const resultBox = document.getElementById("actionResult");
    const orderId = document.getElementById("actionOrderId").value;
    const action = document.getElementById("actionType").value;

    try {
        const result = await apiRequest(`/orders/${orderId}/${action}`, {
            method: "POST",
            body: JSON.stringify({})
        });
        resultBox.classList.remove("empty");
        resultBox.textContent = JSON.stringify(result, null, 2);
    } catch (err) {
        resultBox.classList.remove("empty");
        resultBox.textContent = "Lỗi: " + err.message;
    }
});

initOrders();
