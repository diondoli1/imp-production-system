import React from "react";
import { useMemo, useState } from "react";

import EventTimeline from "../components/EventTimeline";
import MachineStatusBadge from "../components/MachineStatusBadge";
import Panel from "../components/Panel";
import { MACHINE_ID } from "../constants";
import { api } from "../services/api";

const SCRAP_REASONS = [
  "DIMENSION_OUT",
  "SURFACE_DEFECT",
  "WRONG_SETUP",
  "TOOL_MARK",
  "OPERATOR_ERROR",
];

export default function OperatorPage({
  machineState,
  jobs,
  events,
  operatorSession,
  setOperatorSession,
  refreshAll,
}) {
  const [operatorName, setOperatorName] = useState("");
  const [pin, setPin] = useState("");
  const [selectedJob, setSelectedJob] = useState("");
  const [noteText, setNoteText] = useState("");
  const [scrapQty, setScrapQty] = useState(1);
  const [scrapReason, setScrapReason] = useState("DIMENSION_OUT");
  const [scrapNote, setScrapNote] = useState("");
  const [message, setMessage] = useState("");

  const activeJob = useMemo(
    () => jobs.find((job) => job.job_id === machineState.active_job_id) || null,
    [jobs, machineState.active_job_id],
  );

  async function runAction(label, fn) {
    try {
      await fn();
      setMessage(`${label} completed`);
      await refreshAll();
    } catch (error) {
      setMessage(`${label} failed: ${error.message}`);
    }
  }

  return (
    <div className="page-grid">
      <Panel title="Machine Header">
        <p>
          <strong>Machine:</strong> {MACHINE_ID}
        </p>
        <p>
          <strong>Status:</strong> <MachineStatusBadge state={machineState.current_state} />
        </p>
        <p className="message">{message}</p>
      </Panel>

      <Panel title="1) Operator Login">
        <div className="form-row">
          <input
            placeholder="Operator Name"
            value={operatorName}
            onChange={(e) => setOperatorName(e.target.value)}
          />
          <input placeholder="PIN" value={pin} onChange={(e) => setPin(e.target.value)} type="password" />
          <button
            type="button"
            onClick={() =>
              runAction("Login", async () => {
                const result = await api.loginOperator(operatorName, pin);
                setOperatorSession({
                  operator_id: result.data.operator_id,
                  operator_name: result.data.operator_name,
                });
              })
            }
          >
            Login
          </button>
          <button
            type="button"
            onClick={() =>
              operatorSession &&
              runAction("Logout", async () => {
                await api.logoutOperator(operatorSession.operator_id);
                setOperatorSession(null);
              })
            }
          >
            Logout
          </button>
        </div>
        <p>Active operator: {operatorSession?.operator_name || "-"}</p>
      </Panel>

      <Panel title="2) Job Selection List">
        <div className="form-row">
          <select value={selectedJob} onChange={(e) => setSelectedJob(e.target.value)}>
            <option value="">Select job</option>
            {jobs.map((job) => (
              <option key={job.job_id} value={job.job_id}>
                {job.job_id} - {job.part_name}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() =>
              selectedJob &&
              runAction("Select job", () => api.selectJob(selectedJob, operatorSession?.operator_id || null))
            }
          >
            Select Job
          </button>
        </div>
      </Panel>

      <Panel title="3) Drawing Viewer">
        <p>Active job: {activeJob ? `${activeJob.job_id} - ${activeJob.part_name}` : "-"}</p>
        <p>Drawing file: {activeJob?.drawing_file || "-"}</p>
      </Panel>

      <Panel title="4) Machine Control Panel">
        <div className="button-grid">
          <button type="button" onClick={() => runAction("Start Setup", () => api.startSetup(operatorSession?.operator_id || null))}>
            Start Setup
          </button>
          <button
            type="button"
            onClick={() => runAction("Confirm Setup", () => api.confirmSetup(operatorSession?.operator_id || null))}
          >
            Confirm Setup
          </button>
          <button type="button" onClick={() => runAction("Start Cycle", () => api.startCycle(operatorSession?.operator_id || null))}>
            Start Cycle
          </button>
          <button
            type="button"
            onClick={() => runAction("Cycle Complete", () => api.completeCycle(operatorSession?.operator_id || null))}
          >
            Cycle Complete
          </button>
        </div>
      </Panel>

      <Panel title="5) Scrap Reporting Panel">
        <div className="form-row">
          <input
            type="number"
            min="1"
            value={scrapQty}
            onChange={(e) => setScrapQty(Number(e.target.value))}
            placeholder="Quantity"
          />
          <select value={scrapReason} onChange={(e) => setScrapReason(e.target.value)}>
            {SCRAP_REASONS.map((reason) => (
              <option key={reason} value={reason}>
                {reason}
              </option>
            ))}
          </select>
          <input placeholder="Scrap note" value={scrapNote} onChange={(e) => setScrapNote(e.target.value)} />
          <button
            type="button"
            onClick={() =>
              runAction("Report scrap", () =>
                api.reportScrap(scrapQty, scrapReason, scrapNote, operatorSession?.operator_id || null),
              )
            }
          >
            Submit Scrap
          </button>
        </div>
      </Panel>

      <Panel title="6) Operator Notes Panel">
        <div className="form-row">
          <textarea
            rows={3}
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="Operator notes (stored locally in UI shell until backend note route is added)"
          />
          <button type="button" onClick={() => setMessage(`Note captured: ${noteText || "(empty)"}`)}>
            Save Note (UI Shell)
          </button>
        </div>
      </Panel>

      <EventTimeline events={events} />
    </div>
  );
}
