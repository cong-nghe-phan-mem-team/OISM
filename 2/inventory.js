if (!localStorage.getItem("token")) {
    window.location.href = "index.html";
}

function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "index.html";
}

// ==== Tạo phiếu nhập ====
document.getElementById("createReceiptForm").addEventListener("submit", async function (event) {
    event.preventDefault();
    const resultBox = document.getElementById("receiptResult");

    const payload = {
        skuId: document.getElementById("skuId").value,
        branchId: document.getElementById("branchId").value,
        importQuantity: parseInt(document.getElementById("importQuantity").value),
        importUnitPrice: parseFloat(document.getElementById("importUnitPrice").value),
        referenceId: document.getElementById("referenceId").value || null
    };

    try {
        const result = await apiRequest("/inventory/receipts", {
            method: "POST",
            body: JSON.stringify(payload)
        });
        resultBox.classList.remove("empty");
        resultBox.textContent = JSON.stringify(result, null, 2);
    } catch (err) {
        resultBox.classList.remove("empty");
        resultBox.textContent = "Lỗi: " + err.message;
    }
});

// ==== Kiểm tra/xác nhận giao dịch nhập (COGS đã được cập nhật lúc nhập) ====
document.getElementById("confirmReceiptForm").addEventListener("submit", async function (event) {
    event.preventDefault();
    const resultBox = document.getElementById("confirmResult");
    const receiptId = document.getElementById("confirmReceiptId").value;

    try {
        const result = await apiRequest(`/cost/receipts/${receiptId}/confirm`, {
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

// ==== Tra tồn kho khả dụng (RSE) ====
document.getElementById("stockForm").addEventListener("submit", async function (event) {
    event.preventDefault();
    const resultBox = document.getElementById("stockResult");

    const skuId = document.getElementById("stockSkuId").value;
    const branchId = document.getElementById("stockBranchId").value;

    try {
        const result = await apiRequest(
            `/rse/available-stock?sku_id=${skuId}&branch_id=${branchId}`,
            { method: "GET" }
        );
        resultBox.classList.remove("empty");
        resultBox.textContent = JSON.stringify(result, null, 2);
    } catch (err) {
        resultBox.classList.remove("empty");
        resultBox.textContent = "Lỗi: " + err.message;
    }
});

// ==== Xem ledger ====
async function loadLedger() {
    const tableWrap = document.getElementById("ledgerTableWrap");
    const resultBox = document.getElementById("ledgerResult");
    const skuId = document.getElementById("ledgerSkuId").value;

    const url = skuId
        ? `/inventory/ledger?sku_id=${encodeURIComponent(skuId)}`
        : "/inventory/ledger";

    try {
        const result = await apiRequest(url, { method: "GET" });
        const data = result.data || [];

        if (!Array.isArray(data) || data.length === 0) {
            tableWrap.innerHTML = "<p>Chưa có dữ liệu ledger.</p>";
            resultBox.classList.add("empty");
            return;
        }

        let html = "<table class='demo-table'><tr>";
        const keys = Object.keys(data[0]);
        keys.forEach(k => html += `<th>${k}</th>`);
        html += "</tr>";

        data.forEach(row => {
            html += "<tr>";
            keys.forEach(k => html += `<td>${row[k] ?? ""}</td>`);
            html += "</tr>";
        });
        html += "</table>";

        tableWrap.innerHTML = html;
        resultBox.classList.add("empty");

    } catch (err) {
        tableWrap.innerHTML = "";
        resultBox.classList.remove("empty");
        resultBox.textContent = "Lỗi: " + err.message;
    }
}
