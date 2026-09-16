// ==== Kiểm tra đăng nhập ====
if (!localStorage.getItem("token")) {
    window.location.href = "index.html";
}

function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "index.html";
}

let variantCount = 0;


// ==================================================
// QUẢN LÝ VARIANT
// ==================================================

function addVariantRow() {
    const container = document.getElementById("variantsContainer");

    if (!container) return;

    variantCount++;

    const id = variantCount;

    const row = document.createElement("div");

    row.className = "variant-row";
    row.id = "variant-row-" + id;

    row.innerHTML = `
        <div class="form-field">
            <label>SKU</label>
            <input
                type="text"
                class="variant-sku"
                placeholder="e.g. SKU-001"
                required
            >
        </div>

        <div class="form-field">
            <label>Barcode <span>(Optional)</span></label>
            <input
                type="text"
                class="variant-barcode"
                placeholder="Leave blank if not available"
            >
        </div>

        <div class="form-field">
            <label>Retail Price (VND)</label>
            <input
                type="number"
                class="variant-retail"
                placeholder="100000"
                min="0"
                required
            >
        </div>

        <div class="form-field">
            <label>Wholesale Price (VND)</label>
            <input
                type="number"
                class="variant-wholesale"
                placeholder="80000"
                min="0"
                required
            >
        </div>

        <button
            type="button"
            class="danger"
            onclick="removeVariantRow(${id})"
        >
            Remove
        </button>
    `;

    container.appendChild(row);
}


function removeVariantRow(id) {
    const row = document.getElementById("variant-row-" + id);

    if (row) {
        row.remove();
    }
}


function resetVariants() {
    const container = document.getElementById("variantsContainer");

    if (!container) return;

    container.innerHTML = "";

    variantCount = 0;

    addVariantRow();
}


// ==================================================
// TẠO SẢN PHẨM
// ==================================================

document
    .getElementById("createProductForm")
    .addEventListener("submit", async function (event) {

        event.preventDefault();

        const resultBox =
            document.getElementById("createResult");


        // ------------------------------------------
        // Lấy variants
        // ------------------------------------------

        const variants = [];

        document
            .querySelectorAll(".variant-row")
            .forEach(function (row) {

                const sku =
                    row
                        .querySelector(".variant-sku")
                        .value
                        .trim();

                if (!sku) return;

                variants.push({
                    sku: sku,

                    barcode:
                        row
                            .querySelector(".variant-barcode")
                            .value
                            .trim() || null,

                    retailPrice:
                        Number(
                            row
                                .querySelector(".variant-retail")
                                .value || 0
                        ),

                    wholesalePrice:
                        Number(
                            row
                                .querySelector(".variant-wholesale")
                                .value || 0
                        )
                });
            });


        // ------------------------------------------
        // Category
        // ------------------------------------------

        const categoryValue =
            document.getElementById("categoryId").value;


        // ------------------------------------------
        // Brand
        // ------------------------------------------

        const brandValue =
            document.getElementById("brandId").value;


        // ------------------------------------------
        // Payload
        // ------------------------------------------

        const payload = {

            title:
                document
                    .getElementById("title")
                    .value
                    .trim(),

            categoryId:
                categoryValue
                    ? parseInt(categoryValue, 10)
                    : null,

            brandId:
                brandValue
                    ? parseInt(brandValue, 10)
                    : null,

            variants: variants
        };


        // ==================================================
        // GỌI API
        // ==================================================

        try {

            await apiRequest("/products", {

                method: "POST",

                body: JSON.stringify(payload)

            });


            // ==================================================
            // THÀNH CÔNG
            // KHÔNG HIỆN JSON
            // ==================================================

            resultBox.classList.remove("empty");

            resultBox.style.color = "#166534";

            resultBox.style.background = "#f0fdf4";

            resultBox.style.border =
                "1px solid #bbf7d0";

            resultBox.style.padding = "12px";

            resultBox.style.borderRadius = "8px";

            resultBox.style.whiteSpace = "normal";


            resultBox.textContent =
                "✅ Product created successfully!";


            // ------------------------------------------
            // Reload danh sách sản phẩm
            // ------------------------------------------

            await loadProducts();


            // ------------------------------------------
            // Reset variant
            // ------------------------------------------

            resetVariants();


            // ------------------------------------------
            // Tự xóa thông báo sau 3 giây
            // ------------------------------------------

            setTimeout(function () {

                resultBox.classList.add("empty");

                resultBox.textContent = "";

            }, 3000);


        } catch (err) {

            // ==================================================
            // CÓ LỖI
            // ==================================================

            resultBox.classList.remove("empty");

            resultBox.style.color = "#dc2626";

            resultBox.style.background = "#fef2f2";

            resultBox.style.border =
                "1px solid #fecaca";

            resultBox.style.padding = "12px";

            resultBox.style.borderRadius = "8px";

            resultBox.style.whiteSpace = "pre-line";


            resultBox.textContent =
                "❌ Error:\n" + err.message;
        }

    });


// ==================================================
// LOAD DANH SÁCH SẢN PHẨM
// ==================================================

async function loadProducts() {

    const tableWrap =
        document.getElementById("productsTableWrap");

    const resultBox =
        document.getElementById("listResult");


    try {

        const result =
            await apiRequest("/products", {
                method: "GET"
            });


        const data =
            result.data || [];


        // ------------------------------------------
        // Không có sản phẩm
        // ------------------------------------------

        if (!Array.isArray(data) || data.length === 0) {

            tableWrap.innerHTML =
                "<p>Chưa có sản phẩm nào.</p>";

            resultBox.classList.add("empty");

            return;
        }


        // ------------------------------------------
        // Tạo bảng
        // ------------------------------------------

        let html = `
            <table class="demo-table">

                <tr>
                    <th>ID</th>
                    <th>Title</th>
                    <th>Category</th>
                    <th>Brand</th>
                    <th>Variants</th>
                </tr>
        `;


        data.forEach(function (p) {

            html += `
                <tr>

                    <td>${p.id ?? ""}</td>

                    <td>${p.title ?? ""}</td>

                    <td>${p.categoryId ?? ""}</td>

                    <td>${p.brandId ?? ""}</td>

                    <td>
                        ${
                            Array.isArray(p.variants)
                                ? p.variants.length
                                : ""
                        }
                    </td>

                </tr>
            `;

        });


        html += "</table>";


        tableWrap.innerHTML = html;


        resultBox.classList.add("empty");


    } catch (err) {

        tableWrap.innerHTML = "";

        resultBox.classList.remove("empty");

        resultBox.style.color = "#dc2626";

        resultBox.textContent =
            "❌ Lỗi: " + err.message;
    }
}


// ==================================================
// KHỞI TẠO
// ==================================================

addVariantRow();

loadProducts();