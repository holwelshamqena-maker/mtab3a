from pathlib import Path
p=Path('/home/ubuntu/index.html')
s=p.read_text()

# Add UI choice in invoice modal
old='''            <div id=stepSelectType>\n                <p>هل هذه الفاتورة طباعة بنر؟</p>'''
new='''            <div id=stepSelectType>\n                <label style="display:block;text-align:right;font-weight:700;color:#0d3b66">نوع التعامل مع الفاتورة\n                    <select id="invoiceMode" onchange="previewCarryForwardBalance()">\n                        <option value="new">🧾 فاتورة جديدة — ترحيل الرصيد القديم</option>\n                        <option value="append">➕ إضافة على الفواتير القديمة</option>\n                    </select>\n                </label>\n                <div id="carryForwardHint" class="price-hint">سيتم حساب الرصيد القديم وترحيله مع الفاتورة الجديدة عند المشاركة.</div>\n                <p>هل هذه الفاتورة طباعة بنر؟</p>'''
if old not in s: raise SystemExit('step marker not found')
s=s.replace(old,new,1)

# Summary on invoice list
old='''            <div class=loader id=modalInvoicesLoader></div>\n            <div style=overflow-x:auto;margin-top:10px>'''
new='''            <div class=loader id=modalInvoicesLoader></div>\n            <div id="modalCarryForwardSummary" class="carry-forward-summary" style="display:none"></div>\n            <div style=overflow-x:auto;margin-top:10px>'''
if old not in s: raise SystemExit('summary marker not found')
s=s.replace(old,new,1)

# CSS
css='''\n        .carry-forward-summary { background: #e8f4ff; border-right: 4px solid #0d3b66; border-radius: 8px; padding: 12px; margin: 10px 0; color: #0d3b66; font-weight: 700; line-height: 1.9; }\n'''
s=s.replace('        .price-hint { color:#0d3b66; font-size:13px; margin:4px 0; }', '        .price-hint { color:#0d3b66; font-size:13px; margin:4px 0; }'+css,1)

# Add helper functions before displayInvoices
marker='''            // Display invoices in the modal\n            function displayInvoices(invoices) {'''
helper='''            function getClientOutstandingBalance() {\n                return db.ref("invoices/" + currentClientId).once("value").then(snapshot => {\n                    let total = 0, paid = 0;\n                    if (snapshot.exists()) snapshot.forEach(child => {\n                        const item = child.val() || {};\n                        if (item.isPayment) paid += Number(item.amount) || 0;\n                        else total += Number(item.total) || 0;\n                    });\n                    return Math.max(0, total - paid);\n                });\n            }\n            window.previewCarryForwardBalance = function() {\n                const hint = document.getElementById("carryForwardHint");\n                const mode = document.getElementById("invoiceMode").value;\n                if (!hint) return;\n                if (mode === "append") { hint.textContent = "ستضاف الفاتورة إلى الفواتير الحالية بدون إنشاء رصيد مرحّل."; return; }\n                hint.textContent = "جارٍ حساب الرصيد السابق...";\n                getClientOutstandingBalance().then(balance => { hint.textContent = `الرصيد السابق الذي سيُرحّل: ${balance.toFixed(2)} جنيه — سيظهر مع قيمة الفاتورة الجديدة عند المشاركة.`; }).catch(() => { hint.textContent = "سيتم حساب الرصيد السابق عند حفظ الفاتورة."; });\n            };\n            function getInvoiceModeData() {\n                const mode = document.getElementById("invoiceMode")?.value || "append";\n                return mode === "new" ? getClientOutstandingBalance().then(previousBalance => ({ invoiceMode: "new", previousBalance: previousBalance.toFixed(2) })) : Promise.resolve({ invoiceMode: "append", previousBalance: "0.00" });\n            }\n\n            // Display invoices in the modal\n            function displayInvoices(invoices) {'''
if marker not in s: raise SystemExit('display marker not found')
s=s.replace(marker,helper,1)

# add summary variables after totalPaid
old='''                let totalAll = 0;\n                let totalPaid = 0;'''
new='''                let totalAll = 0;\n                let totalPaid = 0;\n                let latestNewInvoice = null;'''
s=s.replace(old,new,1)

# inside non-payment after totalAll += total
old='''                        totalAll += total;\n                        \n                        const length'''
new='''                        totalAll += total;\n                        if (invoice.invoiceMode === "new") {\n                            if (!latestNewInvoice || String(invoice.date || "") >= String(latestNewInvoice.date || "")) latestNewInvoice = invoice;\n                        }\n                        \n                        const length'''
s=s.replace(old,new,1)

# after totalElement assignment before loader
old='''                    totalElement.innerText = totalRemaining.toFixed(2);\n                }\n                \n                loader.style.display = "none";'''
new='''                    totalElement.innerText = totalRemaining.toFixed(2);\n                }\n                const summary = document.getElementById("modalCarryForwardSummary");\n                if (summary) {\n                    if (latestNewInvoice) {\n                        const oldBalance = Number(latestNewInvoice.previousBalance) || 0;\n                        const currentTotal = Number(latestNewInvoice.total) || 0;\n                        summary.innerHTML = `🧾 <strong>آخر فاتورة جديدة</strong><br>الرصيد السابق المُرحّل: ${oldBalance.toFixed(2)} جنيه<br>قيمة الفاتورة الجديدة: ${currentTotal.toFixed(2)} جنيه<br>إجمالي الحساب الحالي: ${totalRemaining.toFixed(2)} جنيه`;\n                        summary.style.display = "block";\n                    } else { summary.style.display = "none"; }\n                }\n                loader.style.display = "none";'''
if old not in s: raise SystemExit('total marker not found')
s=s.replace(old,new,1)

# initialize modal and preview
old='''                document.getElementById("manualForm").style.display = "none";\n                \n                if (window.innerWidth < 768)'''
new='''                document.getElementById("manualForm").style.display = "none";\n                document.getElementById("invoiceMode").value = "new";\n                previewCarryForwardBalance();\n                \n                if (window.innerWidth < 768)'''
s=s.replace(old,new,1)

# banner invoice save: wrap push with mode data
old='''                db.ref("invoices/" + currentClientId).push(invoice).then(() => {\n                    console.log(`Invoice saved for client ${currentClientId}:`, invoice);'''
new='''                getInvoiceModeData().then(modeData => {\n                    Object.assign(invoice, modeData);\n                    return db.ref("invoices/" + currentClientId).push(invoice);\n                }).then(() => {\n                    console.log(`Invoice saved for client ${currentClientId}:`, invoice);'''
# only first occurrence banner
if old not in s: raise SystemExit('banner push not found')
s=s.replace(old,new,1)
# manual occurrence
if old not in s: raise SystemExit('manual push not found')
s=s.replace(old,new,1)

# share report add summary
old='''                        ${document.getElementById("modalInvoiceTable").outerHTML}\n                        <h3 style="font-size: 12pt; text-align: left; margin-top: 5mm;">الإجمـــالي: ${document.getElementById("modalTotalInvoices").innerText} جنيه</h3>'''
new='''                        ${document.getElementById("modalCarryForwardSummary")?.outerHTML || ""}\n                        ${document.getElementById("modalInvoiceTable").outerHTML}\n                        <h3 style="font-size: 12pt; text-align: left; margin-top: 5mm;">إجمالي الحساب (قديم + جديد): ${document.getElementById("modalTotalInvoices").innerText} جنيه</h3>'''
if old not in s: raise SystemExit('share marker not found')
s=s.replace(old,new,1)

# close reset mode and summary
old='''                document.getElementById("unitPrice").value = "";\n                document.getElementById("bannerPricingItem").value = "";'''
new='''                document.getElementById("unitPrice").value = "";\n                document.getElementById("invoiceMode").value = "new";\n                document.getElementById("carryForwardHint").textContent = "سيتم حساب الرصيد القديم وترحيله مع الفاتورة الجديدة عند المشاركة.";\n                document.getElementById("bannerPricingItem").value = "";'''
if old not in s: raise SystemExit('close marker not found')
s=s.replace(old,new,1)

p.write_text(s)
