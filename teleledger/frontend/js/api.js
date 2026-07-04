// Points at your Render backend. Update after deploying.
const API_BASE = "https://teleledger-backend.onrender.com/api";

const tg = window.Telegram?.WebApp;
const RAW_INIT_DATA = tg?.initData || "";

async function apiRequest(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "Authorization": `TelegramWebApp ${RAW_INIT_DATA}`,
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API ${res.status}: ${err}`);
  }
  return res.status === 204 ? null : res.json();
}

const API = {
  dashboard: () => apiRequest("/dashboard/"),
  listTransactions: () => apiRequest("/transactions/"),
  addTransaction: (data) => apiRequest("/transactions/", { method: "POST", body: JSON.stringify(data) }),
  deleteTransaction: (id) => apiRequest(`/transactions/${id}/`, { method: "DELETE" }),

  listCollections: () => apiRequest("/collections/"),
  addCollection: (data) => apiRequest("/collections/", { method: "POST", body: JSON.stringify(data) }),
  settleCollection: (id) => apiRequest(`/collections/${id}/settle/`, { method: "POST" }),

  listReminders: () => apiRequest("/reminders/"),
  addReminder: (data) => apiRequest("/reminders/", { method: "POST", body: JSON.stringify(data) }),
};
