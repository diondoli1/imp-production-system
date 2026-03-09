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
  createJob: (payload) =>
    request("/api/jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  selectJob: (job_id, operator_id) =>
    request("/api/jobs/select", {
      method: "POST",
      body: JSON.stringify({ job_id, operator_id }),
    }),
  finishJob: (operator_id, note = null) =>
    request("/api/jobs/finish", {
      method: "POST",
      body: JSON.stringify({ operator_id, note }),
    }),
  openDrawing: (job_id, operator_id = null) => {
    const query = operator_id ? `?operator_id=${encodeURIComponent(operator_id)}` : "";
    return request(`/api/jobs/${encodeURIComponent(job_id)}/drawing${query}`);
  },
  getCompletedJobsToday: () => request("/api/jobs/completed/today"),
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
  pauseCycle: (operator_id, reason_code, note = null) =>
    request("/api/machine/cycle/pause", {
      method: "POST",
      body: JSON.stringify({ operator_id, reason_code, note }),
    }),
  resumeCycle: (operator_id, note = null) =>
    request("/api/machine/cycle/resume", {
      method: "POST",
      body: JSON.stringify({ operator_id, note }),
    }),
  completeCycle: (operator_id) =>
    request("/api/machine/cycle/complete", {
      method: "POST",
      body: JSON.stringify({ operator_id }),
    }),
  triggerAlarm: (operator_id, reason_code, note = null) =>
    request("/api/machine/alarm/trigger", {
      method: "POST",
      body: JSON.stringify({ operator_id, reason_code, note }),
    }),
  clearAlarm: (operator_id, note = null) =>
    request("/api/machine/alarm/clear", {
      method: "POST",
      body: JSON.stringify({ operator_id, note }),
    }),
  reportScrap: (quantity, reason_code, note, operator_id) =>
    request("/api/production/scrap", {
      method: "POST",
      body: JSON.stringify({ quantity, reason_code, note, operator_id }),
    }),
  addNote: (note, operator_id, reason_code = null) =>
    request("/api/production/note", {
      method: "POST",
      body: JSON.stringify({ note, operator_id, reason_code }),
    }),
  getDashboardSummary: () => request("/api/dashboard/summary"),
  getDashboardEvents: (limit = 50) => request(`/api/dashboard/events?limit=${limit}`),
  getDashboardTimeline: () => request("/api/dashboard/timeline"),
  reasonSuggest: (note, reason_group = "ALARM", job_id = null, operator_id = null) =>
    request("/api/ai/reason-suggest", {
      method: "POST",
      body: JSON.stringify({ note, reason_group, job_id, operator_id }),
    }),
  getAISummary: (payload = {}) =>
    request("/api/ai/summary", {
      method: "POST",
      body: JSON.stringify({ limit: 100, ...payload }),
    }),
  getAIDowntimeAnalysis: (payload = {}) =>
    request("/api/ai/downtime-analysis", {
      method: "POST",
      body: JSON.stringify({ limit: 100, ...payload }),
    }),
  getAIScrapAnalysis: (payload = {}) =>
    request("/api/ai/scrap-analysis", {
      method: "POST",
      body: JSON.stringify({ limit: 100, ...payload }),
    }),
  askAIQuestion: (question, payload = {}) =>
    request("/api/ai/question", {
      method: "POST",
      body: JSON.stringify({ question, limit: 100, ...payload }),
    }),
};
