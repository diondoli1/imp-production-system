import { API_BASE } from "../constants";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json();
}

export const api = {
  loginApp: (name, pin) =>
    request("/api/login", {
      method: "POST",
      body: JSON.stringify({ name, pin }),
    }),
  loginOperator: (operator_name, pin) =>
    request("/api/operators/login", {
      method: "POST",
      body: JSON.stringify({ operator_name, pin }),
    }),
  logoutOperator: (operator_id) =>
    request("/api/operators/logout", {
      method: "POST",
      body: JSON.stringify({ operator_id }),
    }),
  getJobs: () => request("/api/jobs"),
  selectJob: (job_id, operator_id) =>
    request("/api/jobs/select", {
      method: "POST",
      body: JSON.stringify({ job_id, operator_id }),
    }),
  getMachineState: () => request("/api/machine/state"),
  getMachineEvents: (limit = 50) => request(`/api/machine/events?limit=${limit}`),
  startSetup: (operator_id) =>
    request("/api/machine/setup/start", {
      method: "POST",
      body: JSON.stringify({ operator_id }),
    }),
  confirmSetup: (operator_id) =>
    request("/api/machine/setup/confirm", {
      method: "POST",
      body: JSON.stringify({ operator_id }),
    }),
  startCycle: (operator_id) =>
    request("/api/machine/cycle/start", {
      method: "POST",
      body: JSON.stringify({ operator_id }),
    }),
  completeCycle: (operator_id) =>
    request("/api/machine/cycle/complete", {
      method: "POST",
      body: JSON.stringify({ operator_id }),
    }),
  reportScrap: (quantity, reason_code, note, operator_id) =>
    request("/api/production/scrap", {
      method: "POST",
      body: JSON.stringify({ quantity, reason_code, note, operator_id }),
    }),
  getDashboardSummary: () => request("/api/dashboard/summary"),
  getDashboardEvents: (limit = 50) => request(`/api/dashboard/events?limit=${limit}`),
  getAIPlaceholder: () =>
    request("/api/ai/placeholder-report", {
      method: "POST",
      body: JSON.stringify({}),
    }),
};