from pathlib import Path

src = Path('/home/ubuntu/upload/pasted_content.txt').read_text()

# Client type options
src = src.replace('''<select id=clientType>\n            <option value=مكتب>مكتب</option>\n            <option value=فرد>فرد</option>\n        </select>''', '''<select id=clientType>\n            <option value=مكتب>مكتب</option>\n            <option value=فرد>فرد</option>\n            <option value=تجاري>تجاري</option>\n        </select>''')
src = src.replace('''<select id="editClientType">\n                <option value="مكتب">مكتب</option>\n                <option value="فرد">فرد</option>\n            </select>''', '''<select id="editClientType">\n                <option value="مكتب">مكتب</option>\n                <option value="فرد">فرد</option>\n                <option value="تجاري">تجاري</option>\n            </select>''')

# Navigation button
src = src.replace('<button onclick=goToSalaries()>مرتبات</button>', '<button onclick=goToPricingPage()>قائمة الأسعار</button>\n        <button onclick=goToSalaries()>مرتبات</button>')

# Pricing page before invoice box
pricing_html = r'''
    <div style="display:none" id="pricingSection" class="box">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap">
            <h3 style="margin:0">📋 قائمة الأصناف والأسعار</h3>
            <button onclick="goToHomePage()">⬅️ العودة للعملاء</button>
        </div>
        <p style="color:#555">أضف سعرًا خاصًا لكل صنف حسب نوع العميل. ستظهر الأصناف تلقائيًا عند إضافة فاتورة للعميل.</p>
        <div class="pricing-form" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;align-items:end">
            <label>نوع العميل<select id="pricingClientType"><option value="فرد">فرد</option><option value="مكتب">مكتب</option><option value="تجاري">تجاري</option></select></label>
            <label>اسم الصنف<input id="pricingItemName" type="text" placeholder="مثال: كارت شخصي"></label>
            <label>الوحدة<input id="pricingItemUnit" type="text" placeholder="قطعة / متر"></label>
            <label>السعر<input id="pricingItemPrice" type="number" min="0" step="0.01" placeholder="السعر بالجنيه"></label>
            <button onclick="savePricingItem()">➕ إضافة الصنف</button>
        </div>
        <div class="client-filter-buttons" style="justify-content:flex-start">
            <button class="client-filter-button active" data-pricing-filter="all" onclick="filterPricing('all')">كل الأسعار</button>
            <button class="client-filter-button" data-pricing-filter="فرد" onclick="filterPricing('فرد')">فرد</button>
            <button class="client-filter-button" data-pricing-filter="مكتب" onclick="filterPricing('مكتب')">مكتب</button>
            <button class="client-filter-button" data-pricing-filter="تجاري" onclick="filterPricing('تجاري')">تجاري</button>
        </div>
        <div class="loader" id="pricingLoader"></div>
        <div style="overflow-x:auto"><table id="pricingTable"><thead><tr><th>نوع العميل</th><th>الصنف</th><th>الوحدة</th><th>السعر</th><th>إجراء</th></tr></thead><tbody></tbody></table></div>
        <p id="pricingEmpty" style="text-align:center;color:#777;display:none">لا توجد أسعار مضافة حتى الآن.</p>
    </div>
'''
src = src.replace('    <div style=display:none id=invoiceBox class=box>', pricing_html + '    <div style=display:none id=invoiceBox class=box>', 1)

# Pricing dropdowns in invoice forms
src = src.replace('''<div class="description-field">\n                    <label for="bannerDesc">الوصف (اسم الخامة):</label>''', '''<label>الصنف من قائمة الأسعار<select id="bannerPricingItem" onchange="applyPricingToInvoice('banner')"><option value="">-- سعر يدوي / اختر صنفًا --</option></select></label>\n                <div class="description-field">\n                    <label for="bannerDesc">الوصف (اسم الخامة):</label>''')
src = src.replace('''<div class=hidden id=manualForm>\n                <input placeholder=الوصف id=desc type=text />''', '''<div class=hidden id=manualForm>\n                <label>الصنف من قائمة الأسعار<select id="manualPricingItem" onchange="applyPricingToInvoice('manual')"><option value="">-- اختر صنفًا --</option></select></label>\n                <input placeholder=الوصف id=desc type=text />''')

# CSS
css = r'''
        .pricing-form label { display:block; font-weight:700; color:#0d3b66; }
        .pricing-form input, .pricing-form select { box-sizing:border-box; }
        #pricingTable td, #pricingTable th { white-space:nowrap; }
        .price-hint { color:#0d3b66; font-size:13px; margin:4px 0; }
'''
src = src.replace('    </style>', css + '    </style>', 1)

# Reset dropdowns on close
src = src.replace('''document.getElementById("unitPrice").value = "";\n            };''', '''document.getElementById("unitPrice").value = "";\n                document.getElementById("bannerPricingItem").value = "";\n                document.getElementById("manualPricingItem").value = "";\n            };''', 1)

# Add pricing functions before goToSalaries
marker = '''            window.goToSalaries = function() {'''
functions = r'''
            // Pricing catalog: stored in Firebase under pricingCatalog/{clientType}/{itemId}
            let pricingItems = {};
            let pricingFilter = "all";
            let currentClientType = "";

            function pricingRef() { return db.ref("pricingCatalog"); }
            function escapeHtml(value) {
                return String(value ?? "").replace(/[&<>'"]/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[ch]));
            }
            function loadPricingCatalog(callback) {
                const loader = document.getElementById("pricingLoader");
                if (loader) loader.style.display = "block";
                pricingRef().once("value").then(snapshot => {
                    pricingItems = snapshot.val() || {};
                    if (loader) loader.style.display = "none";
                    renderPricingTable();
                    populateInvoicePricing();
                    if (callback) callback();
                }).catch(error => {
                    if (loader) loader.style.display = "none";
                    console.error("Error loading pricing catalog:", error);
                    showAlert("خطأ", "تعذر تحميل قائمة الأسعار: " + error.message, "error");
                });
            }
            function renderPricingTable() {
                const body = document.querySelector("#pricingTable tbody");
                const empty = document.getElementById("pricingEmpty");
                if (!body) return;
                body.innerHTML = "";
                let count = 0;
                Object.keys(pricingItems).forEach(type => {
                    if (pricingFilter !== "all" && pricingFilter !== type) return;
                    Object.keys(pricingItems[type] || {}).forEach(id => {
                        const item = pricingItems[type][id]; count++;
                        const row = document.createElement("tr");
                        row.innerHTML = `<td>${escapeHtml(type)}</td><td>${escapeHtml(item.name)}</td><td>${escapeHtml(item.unit || "")}</td><td>${Number(item.price || 0).toFixed(2)} جنيه</td><td><button class="edit-btn" onclick="deletePricingItem('${type}','${id}')">حذف</button></td>`;
                        body.appendChild(row);
                    });
                });
                if (empty) empty.style.display = count ? "none" : "block";
            }
            function populateInvoicePricing() {
                ["manualPricingItem", "bannerPricingItem"].forEach(id => {
                    const select = document.getElementById(id); if (!select) return;
                    const selected = select.value; select.innerHTML = '<option value="">-- اختر صنفًا من التسعيرة --</option>';
                    const catalog = pricingItems[currentClientType] || {};
                    Object.keys(catalog).forEach(itemId => {
                        const item = catalog[itemId];
                        const option = document.createElement("option"); option.value = itemId; option.textContent = `${item.name} — ${Number(item.price || 0).toFixed(2)} جنيه${item.unit ? " / " + item.unit : ""}`;
                        option.dataset.price = item.price; option.dataset.name = item.name; select.appendChild(option);
                    });
                    if ([...select.options].some(o => o.value === selected)) select.value = selected;
                });
            }
            window.applyPricingToInvoice = function(kind) {
                const select = document.getElementById(kind === "banner" ? "bannerPricingItem" : "manualPricingItem");
                const option = select && select.options[select.selectedIndex]; if (!option || !option.value) return;
                const price = option.dataset.price || "";
                if (kind === "banner") { document.getElementById("price").value = price; if (!document.getElementById("bannerDesc").value) document.getElementById("bannerDesc").value = option.dataset.name || ""; }
                else { document.getElementById("unitPrice").value = price; document.getElementById("desc").value = option.dataset.name || ""; }
            };
            window.savePricingItem = function() {
                const type = document.getElementById("pricingClientType").value;
                const name = document.getElementById("pricingItemName").value.trim();
                const unit = document.getElementById("pricingItemUnit").value.trim();
                const price = parseFloat(document.getElementById("pricingItemPrice").value);
                if (!name || !unit || !Number.isFinite(price) || price < 0) return showAlert("خطأ", "أدخل نوع العميل والصنف والوحدة والسعر بشكل صحيح", "error");
                pricingRef().child(type).push({ name, unit, price: price.toFixed(2), createdAt: new Date().toISOString() }).then(() => {
                    document.getElementById("pricingItemName").value = ""; document.getElementById("pricingItemUnit").value = ""; document.getElementById("pricingItemPrice").value = "";
                    showAlert("تم بنجاح", "تمت إضافة الصنف إلى قائمة الأسعار", "success"); loadPricingCatalog();
                }).catch(error => showAlert("خطأ", "تعذر حفظ السعر: " + error.message, "error"));
            };
            window.deletePricingItem = function(type, id) {
                Swal.fire({ title:"تأكيد الحذف", text:"هل تريد حذف هذا الصنف من التسعيرة؟", icon:"warning", showCancelButton:true, confirmButtonText:"نعم، احذف", cancelButtonText:"إلغاء" }).then(result => {
                    if (result.isConfirmed) pricingRef().child(type).child(id).remove().then(loadPricingCatalog);
                });
            };
            window.filterPricing = function(filter) { pricingFilter = filter; document.querySelectorAll("[data-pricing-filter]").forEach(btn => btn.classList.toggle("active", btn.dataset.pricingFilter === filter)); renderPricingTable(); };
            window.goToPricingPage = function() {
                if (!isLoggedIn) return showAlert("خطأ", "يرجى تسجيل الدخول أولاً", "error");
                ["statsBox","addClientBox","clientsSection","invoiceBox"].forEach(id => { const el=document.getElementById(id); if(el) el.style.display="none"; });
                document.getElementById("pricingSection").style.display = "block";
                loadPricingCatalog();
                if (window.innerWidth < 768) { document.getElementById("navbar").classList.remove("open"); document.getElementById("sidebarBackdrop").classList.remove("open"); }
            };

'''
src = src.replace(marker, functions + marker, 1)

# Go home hide pricing section
src = src.replace('''                const invoiceBox = document.getElementById("invoiceBox");\n                const addInvoiceBtn''', '''                const invoiceBox = document.getElementById("invoiceBox");\n                const pricingSection = document.getElementById("pricingSection");\n                if (pricingSection) pricingSection.style.display = "none";\n                const addInvoiceBtn''', 1)

# showInvoices load client type, then pricing
old = '''                currentClientId = clientId;\n                currentClientName = clientName;\n                \n                const modal = document.getElementById("invoicesModal");'''
new = '''                currentClientId = clientId;\n                currentClientName = clientName;\n                db.ref("clients/" + clientId).once("value").then(snapshot => { currentClientType = (snapshot.val() || {}).clientType || "مكتب"; populateInvoicePricing(); });\n                \n                const modal = document.getElementById("invoicesModal");'''
src = src.replace(old, new, 1)

# reset client type after adding
src = src.replace('document.getElementById("clientType").value = "مكتب";', 'document.getElementById("clientType").value = "مكتب";', 1)

# ensure pricing hidden on login/logout areas by add to logout hide
src = src.replace('''                    const invoiceBox = document.getElementById("invoiceBox");\n                    const loginUser''', '''                    const invoiceBox = document.getElementById("invoiceBox");\n                    const pricingSection = document.getElementById("pricingSection");\n                    const loginUser''', 1)
src = src.replace('''                    invoiceBox.style.display = "none";\n                    \n                    loginUser.value''', '''                    invoiceBox.style.display = "none";\n                    if (pricingSection) pricingSection.style.display = "none";\n                    \n                    loginUser.value''', 1)

Path('/home/ubuntu/index.html').write_text(src)
