const appEl = document.getElementById("app");
const loadingEl = document.getElementById("loading-screen");
const loadingText = document.getElementById("loading-text");

// --- Telegram WebApp bootstrap (PRD 4.1) ---
if (tg) {
  tg.ready();
  tg.expand();
  const u = tg.initDataUnsafe?.user;
  if (u) document.getElementById("username").textContent = `@${u.username || u.first_name}`;
}

const fmt = (n) => `₹${Number(n).toFixed(2)}`;

// --- Cold-start UX (PRD 7): ping backend, show elapsed-time message ---
async function warmUpBackend() {
  const start = Date.now();
  const tick = setInterval(() => {
    const secs = Math.floor((Date.now() - start) / 1000);
    if (secs > 5) loadingText.textContent = `Waking up the server… (${secs}s, free-tier cold start)`;
  }, 1000);
  try {
    await API.dashboard();
  } finally {
    clearInterval(tick);
    loadingEl.classList.add("hidden");
  }
}

// --- Tab routing ---
const tabs = document.querySelectorAll(".tab-btn");
tabs.forEach((btn) => btn.addEventListener("click", () => renderTab(btn.dataset.tab)));

async function renderTab(tab) {
  tabs.forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
  appEl.innerHTML = `<p class="text-center text-gray-400 mt-8">Loading…</p>`;
  try {
    if (tab === "dashboard") await renderDashboard();
    else if (tab === "add") renderAddForm();
    else if (tab === "collections") await renderCollections();
    else if (tab === "notes") await renderNotes();
  } catch (e) {
    appEl.innerHTML = `<p class="text-red-500 text-sm mt-4">${e.message}</p>`;
  }
}

// --- Dashboard (PRD 4.2: live balance metrics) ---
async function renderDashboard() {
  const data = await API.dashboard();
  appEl.innerHTML = `
    <div class="balance-card bg-emerald-600 text-white mb-3">
      <p class="text-sm opacity-80">Net Available Balance</p>
      <p class="text-3xl font-bold">${fmt(data.net_balance)}</p>
    </div>
    <div class="flex gap-3 mb-4">
      <div class="card flex-1"><p class="text-xs text-gray-400">Cash</p><p class="text-lg font-semibold balance-positive">${fmt(data.cash_balance)}</p></div>
      <div class="card flex-1"><p class="text-xs text-gray-400">Online</p><p class="text-lg font-semibold balance-positive">${fmt(data.online_balance)}</p></div>
    </div>
    <h2 class="font-semibold mb-2 text-sm">Recent Transactions</h2>
    ${data.recent_transactions.map(txCard).join("") || '<p class="text-gray-400 text-sm">No transactions yet.</p>'}
  `;
}

function txCard(t) {
  const sign = t.type === "income" ? "+" : "-";
  const cls = t.type === "income" ? "balance-positive" : "balance-negative";
  return `<div class="card flex justify-between items-center">
    <div><p class="font-medium text-sm">${t.category}</p><p class="text-xs text-gray-400">${t.method} · ${new Date(t.created_at).toLocaleDateString()}</p></div>
    <p class="font-semibold ${cls}">${sign}${fmt(t.amount)}</p>
  </div>`;
}

// --- Add New (PRD 4.2 simplified input, <3s logging) ---
function renderAddForm() {
  appEl.innerHTML = `
    <form id="tx-form" class="card">
      <label class="text-xs text-gray-500">Amount</label>
      <input type="number" step="0.01" name="amount" required placeholder="0.00">
      <label class="text-xs text-gray-500">Type</label>
      <select name="type"><option value="expense">Expense</option><option value="income">Income</option></select>
      <label class="text-xs text-gray-500">Method</label>
      <select name="method"><option value="cash">Cash</option><option value="online">Online</option></select>
      <label class="text-xs text-gray-500">Category</label>
      <input type="text" name="category" required placeholder="Food, Rent, Salary…">
      <label class="text-xs text-gray-500">Notes</label>
      <textarea name="notes" rows="2" placeholder="Optional"></textarea>
      <button type="submit" class="primary">Save Transaction</button>
    </form>
  `;
  document.getElementById("tx-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    await API.addTransaction(Object.fromEntries(fd.entries()));
    tg?.HapticFeedback?.notificationOccurred("success");
    renderTab("dashboard");
  });
}

// --- Collections (PRD 4.3) ---
async function renderCollections() {
  const items = await API.listCollections();
  appEl.innerHTML = `
    <button id="new-collection-btn" class="primary mb-3">+ New Collection Entry</button>
    ${items.map(collectionCard).join("") || '<p class="text-gray-400 text-sm">No collections yet.</p>'}
  `;
  document.getElementById("new-collection-btn").addEventListener("click", renderCollectionForm);
  items.forEach((c) => {
    if (!c.is_settled) {
      document.getElementById(`settle-${c.id}`)?.addEventListener("click", async () => {
        await API.settleCollection(c.id);
        renderTab("collections");
      });
    }
  });
}

function collectionCard(c) {
  const cls = c.type === "to_receive" ? "balance-positive" : "balance-negative";
  const label = c.type === "to_receive" ? "To Receive" : "To Give";
  return `<div class="card flex justify-between items-center">
    <div>
      <p class="font-medium text-sm">${c.person_name}</p>
      <p class="text-xs text-gray-400">${label}${c.due_date ? " · due " + new Date(c.due_date).toLocaleDateString() : ""}</p>
    </div>
    <div class="text-right">
      <p class="font-semibold ${cls}">${fmt(c.amount)}</p>
      ${c.is_settled
        ? '<span class="text-xs text-gray-400">Settled ✓</span>'
        : `<button id="settle-${c.id}" class="text-xs text-emerald-600 underline">Mark Settled</button>`}
    </div>
  </div>`;
}

function renderCollectionForm() {
  appEl.innerHTML = `
    <form id="col-form" class="card">
      <label class="text-xs text-gray-500">Person Name</label>
      <input type="text" name="person_name" required>
      <label class="text-xs text-gray-500">Amount</label>
      <input type="number" step="0.01" name="amount" required>
      <label class="text-xs text-gray-500">Type</label>
      <select name="type"><option value="to_receive">To Receive</option><option value="to_give">To Give</option></select>
      <label class="text-xs text-gray-500">Due Date</label>
      <input type="date" name="due_date">
      <button type="submit" class="primary">Save</button>
    </form>
  `;
  document.getElementById("col-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    await API.addCollection(Object.fromEntries(fd.entries()));
    renderTab("collections");
  });
}

// --- Notes & Reminders (PRD 4.4) ---
async function renderNotes() {
  const items = await API.listReminders();
  appEl.innerHTML = `
    <button id="new-reminder-btn" class="primary mb-3">+ New Reminder</button>
    ${items.map(reminderCard).join("") || '<p class="text-gray-400 text-sm">No reminders yet.</p>'}
  `;
  document.getElementById("new-reminder-btn").addEventListener("click", renderReminderForm);
}

function reminderCard(r) {
  return `<div class="card">
    <p class="text-sm">${r.note_content}</p>
    <p class="text-xs text-gray-400 mt-1">⏰ ${new Date(r.remind_at).toLocaleString()} ${r.is_sent ? "· sent ✓" : ""}</p>
  </div>`;
}

function renderReminderForm() {
  appEl.innerHTML = `
    <form id="rem-form" class="card">
      <label class="text-xs text-gray-500">Note</label>
      <textarea name="note_content" rows="3" required></textarea>
      <label class="text-xs text-gray-500">Remind At</label>
      <input type="datetime-local" name="remind_at" required>
      <button type="submit" class="primary">Save Reminder</button>
    </form>
  `;
  document.getElementById("rem-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    await API.addReminder(Object.fromEntries(fd.entries()));
    renderTab("notes");
  });
}

// --- Boot ---
warmUpBackend().then(() => renderTab("dashboard"));
