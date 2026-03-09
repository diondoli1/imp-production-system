import React, { useEffect, useMemo, useState } from "react";

import EventTimeline from "../components/EventTimeline";
import MachineStatusBadge from "../components/MachineStatusBadge";
import Panel from "../components/Panel";
import { MACHINE_ID } from "../constants";
import { api } from "../services/api";

const TIMELINE_COLORS = {
  IDLE: "#5f6c7b",
  SETUP: "#2f6fbd",
  READY: "#2ba8b7",
  RUNNING: "#1f9d55",
  PAUSED: "#e0a100",
  ALARM: "#d64545",
  COMPLETED: "#6b7cd4",
};

const EMPTY_COMPLETED = {
  jobs_completed_today: 0,
  parts_produced_today: 0,
  scrap_today: 0,
  jobs: [],
};

const DEFAULT_NEW_JOB = {
  part_name: "",
  material: "",
  target_quantity: 10,
  drawing_file: "/drawings/support_plate.pdf",
  planned_cycle_time_sec: 180,
};

function formatDateTime(value) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}

function formatDuration(seconds) {
  const total = Math.max(0, Number(seconds) || 0);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const remainingSeconds = total % 60;
  if (hours > 0) {
    return `${hours}h ${minutes}m ${remainingSeconds}s`;
  }
  if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`;
  }
  return `${remainingSeconds}s`;
}

export default function DashboardPage({ machineState, events, wsStatus, refreshAll }) {
  const [summary, setSummary] = useState(null);
  const [completedJobs, setCompletedJobs] = useState(EMPTY_COMPLETED);
  const [timeline, setTimeline] = useState([]);
  const [loadError, setLoadError] = useState("");

  const [newJob, setNewJob] = useState(DEFAULT_NEW_JOB);
  const [jobCreateStatus, setJobCreateStatus] = useState("");

  const [aiStatus, setAIStatus] = useState("");
  const [aiLoading, setAILoading] = useState(false);
  const [aiReports, setAIReports] = useState([]);
  const [aiQuestion, setAIQuestion] = useState("");

  async function loadDashboardData() {
    try {
      const [summaryPayload, completedPayload, timelinePayload] = await Promise.all([
        api.getDashboardSummary(),
        api.getCompletedJobsToday(),
        api.getDashboardTimeline(),
      ]);
      setSummary(summaryPayload);
      setCompletedJobs(completedPayload || EMPTY_COMPLETED);
      setTimeline(Array.isArray(timelinePayload) ? timelinePayload : []);
      setLoadError("");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load dashboard data";
      setLoadError(message);
    }
  }

  useEffect(() => {
    loadDashboardData().catch(() => {});
  }, [machineState.current_state, machineState.active_job_id, machineState.produced_count, machineState.scrap_count]);

  const runtimeStats = useMemo(() => {
    const stats = {
      running_sec: 0,
      paused_sec: 0,
      alarm_sec: 0,
      setup_sec: 0,
      total_sec: 0,
    };
    for (const segment of timeline) {
      const duration = Number(segment.duration_sec) || 0;
      stats.total_sec += duration;
      if (segment.state === "RUNNING") {
        stats.running_sec += duration;
      }
      if (segment.state === "PAUSED") {
        stats.paused_sec += duration;
      }
      if (segment.state === "ALARM") {
        stats.alarm_sec += duration;
      }
      if (segment.state === "SETUP") {
        stats.setup_sec += duration;
      }
    }
    stats.downtime_sec = stats.paused_sec + stats.alarm_sec + stats.setup_sec;
    return stats;
  }, [timeline]);

  const activeSummary = summary || {
    machine_id: MACHINE_ID,
    current_state: machineState.current_state,
    active_job_id: machineState.active_job_id,
    active_operator_id: machineState.active_operator_id,
    produced_count: machineState.produced_count,
    scrap_count: machineState.scrap_count,
    jobs_completed_today: completedJobs.jobs_completed_today,
    parts_produced_today: completedJobs.parts_produced_today,
    scrap_today: completedJobs.scrap_today,
    updated_at: machineState.updated_at,
  };

  async function handleCreateJob(event) {
    event.preventDefault();
    setJobCreateStatus("");

    const payload = {
      ...newJob,
      target_quantity: Number(newJob.target_quantity),
      planned_cycle_time_sec: newJob.planned_cycle_time_sec ? Number(newJob.planned_cycle_time_sec) : null,
    };

    try {
      const result = await api.createJob(payload);
      setJobCreateStatus(`Created ${result?.data?.job_id || "new job"}`);
      setNewJob(DEFAULT_NEW_JOB);
      await loadDashboardData();
      if (refreshAll) {
        await refreshAll();
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to create job";
      setJobCreateStatus(`Create job failed: ${message}`);
    }
  }

  function addAIReport(result) {
    if (!result) {
      return;
    }
    setAIReports((existing) => [result, ...existing].slice(0, 6));
  }

  async function runAIAction(label, action) {
    setAILoading(true);
    setAIStatus("");
    try {
      const result = await action();
      addAIReport(result);
      setAIStatus(`${label} generated`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "AI request failed";
      setAIStatus(`${label} failed: ${message}`);
    } finally {
      setAILoading(false);
    }
  }

  return (
    <div className="dashboard-layout">
      <Panel title="Machine Status">
        <p>
          <strong>Machine:</strong> {activeSummary.machine_id || MACHINE_ID}
        </p>
        <p>
          <strong>State:</strong> <MachineStatusBadge state={activeSummary.current_state} />
        </p>
        <p>
          <strong>Active Operator:</strong> {activeSummary.active_operator_name || activeSummary.active_operator_id || "-"}
        </p>
        <p>
          <strong>Active Job:</strong>{" "}
          {activeSummary.active_job_id
            ? `${activeSummary.active_job_id}${activeSummary.active_job_name ? ` - ${activeSummary.active_job_name}` : ""}`
            : "-"}
        </p>
        <p>
          <strong>WebSocket:</strong> {wsStatus}
        </p>
        <p>
          <strong>Updated:</strong> {formatDateTime(activeSummary.updated_at)}
        </p>
        {loadError ? <p className="message">Load warning: {loadError}</p> : null}
      </Panel>

      <Panel title="Production KPIs">
        <div className="kpi-grid">
          <div className="kpi-card">
            <small>Produced (Active Job)</small>
            <strong>{activeSummary.produced_count ?? 0}</strong>
          </div>
          <div className="kpi-card">
            <small>Scrap (Active Job)</small>
            <strong>{activeSummary.scrap_count ?? 0}</strong>
          </div>
          <div className="kpi-card">
            <small>Jobs Completed Today</small>
            <strong>{completedJobs.jobs_completed_today ?? 0}</strong>
          </div>
          <div className="kpi-card">
            <small>Parts Produced Today</small>
            <strong>{completedJobs.parts_produced_today ?? 0}</strong>
          </div>
          <div className="kpi-card">
            <small>Scrap Today</small>
            <strong>{completedJobs.scrap_today ?? 0}</strong>
          </div>
          <div className="kpi-card">
            <small>Runtime vs Downtime</small>
            <strong>
              {formatDuration(runtimeStats.running_sec)} / {formatDuration(runtimeStats.downtime_sec)}
            </strong>
          </div>
        </div>
      </Panel>

      <Panel title="Add Job Form">
        <form className="stack" onSubmit={handleCreateJob}>
          <div className="form-row">
            <input
              required
              value={newJob.part_name}
              onChange={(event) => setNewJob((prev) => ({ ...prev, part_name: event.target.value }))}
              placeholder="Part Name"
            />
            <input
              required
              value={newJob.material}
              onChange={(event) => setNewJob((prev) => ({ ...prev, material: event.target.value }))}
              placeholder="Material"
            />
          </div>
          <div className="form-row">
            <input
              required
              min="1"
              type="number"
              value={newJob.target_quantity}
              onChange={(event) => setNewJob((prev) => ({ ...prev, target_quantity: event.target.value }))}
              placeholder="Target Quantity"
            />
            <input
              min="1"
              type="number"
              value={newJob.planned_cycle_time_sec}
              onChange={(event) => setNewJob((prev) => ({ ...prev, planned_cycle_time_sec: event.target.value }))}
              placeholder="Planned Cycle Time (sec)"
            />
          </div>
          <input
            required
            value={newJob.drawing_file}
            onChange={(event) => setNewJob((prev) => ({ ...prev, drawing_file: event.target.value }))}
            placeholder="Drawing File (example: /drawings/support_plate.pdf)"
          />
          <div className="form-row">
            <button type="submit">Create Job</button>
            <span className="message">{jobCreateStatus}</span>
          </div>
        </form>
      </Panel>

      <Panel title="Completed Jobs Today">
        <div className="table-wrap">
          <table className="jobs-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Job</th>
                <th>Produced</th>
                <th>Scrap</th>
                <th>Operator</th>
              </tr>
            </thead>
            <tbody>
              {completedJobs.jobs && completedJobs.jobs.length > 0 ? (
                completedJobs.jobs.map((job) => (
                  <tr key={`${job.job_id}-${job.completed_at}`}>
                    <td>{formatDateTime(job.completed_time || job.completed_at)}</td>
                    <td>{job.job_id}</td>
                    <td>{job.produced_quantity_final}</td>
                    <td>{job.scrap_quantity_final}</td>
                    <td>{job.completed_by_operator_name || job.operator_name || job.completed_by_operator_id || "-"}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5}>No completed jobs recorded today.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="Shift Timeline">
        <div className="shift-timeline" role="img" aria-label="Shift timeline by machine state">
          {timeline.length > 0 ? (
            timeline.map((segment, index) => {
              const widthWeight = Math.max(1, Number(segment.duration_sec) || 1);
              const color = TIMELINE_COLORS[segment.state] || "#5f6c7b";
              const tip = [
                `State: ${segment.state}`,
                `Start: ${formatDateTime(segment.start)}`,
                `End: ${formatDateTime(segment.end)}`,
                `Duration: ${formatDuration(segment.duration_sec)}`,
                `Reason: ${segment.reason_code || "-"}`,
              ].join(" | ");
              return (
                <div
                  key={`${segment.state}-${segment.start}-${index}`}
                  className="shift-segment"
                  style={{ flex: widthWeight, background: color }}
                  title={tip}
                >
                  <span>{segment.state}</span>
                </div>
              );
            })
          ) : (
            <div className="shift-empty">No timeline segments yet.</div>
          )}
        </div>
      </Panel>

      <Panel title="AI Insights">
        <div className="stack">
          <div className="button-grid">
            <button type="button" disabled={aiLoading} onClick={() => runAIAction("Summary", () => api.getAISummary())}>
              Shift Summary
            </button>
            <button type="button" disabled={aiLoading} onClick={() => runAIAction("Downtime", () => api.getAIDowntimeAnalysis())}>
              Downtime Analysis
            </button>
            <button type="button" disabled={aiLoading} onClick={() => runAIAction("Scrap", () => api.getAIScrapAnalysis())}>
              Scrap Insights
            </button>
          </div>
          <div className="form-row">
            <input
              value={aiQuestion}
              onChange={(event) => setAIQuestion(event.target.value)}
              placeholder="Ask AI about machine activity"
            />
            <button
              type="button"
              disabled={aiLoading || !aiQuestion.trim()}
              onClick={() =>
                runAIAction("Question", async () => {
                  const result = await api.askAIQuestion(aiQuestion.trim());
                  setAIQuestion("");
                  return result;
                })
              }
            >
              Ask
            </button>
          </div>
          <p className="message">{aiStatus}</p>
          <div className="ai-report-list">
            {aiReports.length > 0 ? (
              aiReports.map((report) => (
                <article key={report.report_id} className="ai-report-card">
                  <strong>
                    {report.report_type} #{report.report_id}
                  </strong>
                  <small>{report.machine_id}</small>
                  <p>{report.output_text}</p>
                </article>
              ))
            ) : (
              <p className="message">No AI insights generated yet.</p>
            )}
          </div>
        </div>
      </Panel>

      <EventTimeline events={events} />
    </div>
  );
}
