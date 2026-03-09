import React, { useMemo, useState } from "react";

import EventTimeline from "../components/EventTimeline";
import MachineStatusBadge from "../components/MachineStatusBadge";
import Panel from "../components/Panel";
import { MACHINE_ID } from "../constants";
import { api } from "../services/api";

const SCRAP_REASONS = ["DIMENSION_OUT", "SURFACE_DEFECT", "WRONG_SETUP", "TOOL_MARK", "OPERATOR_ERROR"];
const PAUSE_REASONS = [
  "TOOL_CHANGE",
  "INSPECTION",
  "DRAWING_REVIEW",
  "MATERIAL_CHECK",
  "WAITING_INSTRUCTIONS",
  "OPERATOR_BREAK",
];
const ALARM_REASONS = ["TOOL_WEAR", "PROGRAM_STOP", "FIXTURE_ISSUE", "DIMENSION_CHECK", "UNKNOWN_FAULT"];

export default function OperatorPage({ machineState, jobs, events, operatorSession, refreshAll }) {
  const [selectedJob, setSelectedJob] = useState("");
  const [controlNote, setControlNote] = useState("");
  const [pauseReason, setPauseReason] = useState("TOOL_CHANGE");
  const [alarmReason, setAlarmReason] = useState("TOOL_WEAR");
  const [noteText, setNoteText] = useState("");
  const [scrapQty, setScrapQty] = useState(1);
  const [scrapReason, setScrapReason] = useState("DIMENSION_OUT");
  const [scrapNote, setScrapNote] = useState("");
  const [message, setMessage] = useState("");

  const activeJob = useMemo(
    () => jobs.find((job) => job.job_id === machineState.active_job_id) || null,
    [jobs, machineState.active_job_id],
  );

  const operatorId = operatorSession?.operator_id || null;
  const hasOperator = Boolean(operatorId);
  const hasActiveJob = Boolean(activeJob);
  const currentState = machineState.current_state;

  const canSelectJob = hasOperator && currentState === "IDLE";
  const canStartSetup = hasOperator && hasActiveJob && currentState === "IDLE";
  const canConfirmSetup = hasOperator && hasActiveJob && currentState === "SETUP";
  const canStartCycle = hasOperator && hasActiveJob && currentState === "READY";
  const canPauseCycle = hasOperator && hasActiveJob && currentState === "RUNNING";
  const canResumeCycle = hasOperator && hasActiveJob && currentState === "PAUSED";
  const canTriggerAlarm = hasOperator && hasActiveJob && currentState === "RUNNING";
  const canClearAlarm = hasOperator && hasActiveJob && currentState === "ALARM";
  const canCompletePart = hasOperator && hasActiveJob && currentState === "RUNNING";
  const canFinishJob = hasOperator && hasActiveJob && currentState === "RUNNING";
  const canAddNote = hasOperator && hasActiveJob;
  const canReportScrap = hasOperator && hasActiveJob;

  async function runAction(label, fn, onSuccess) {
    try {
      await fn();
      setMessage(`${label} completed`);
      if (onSuccess) {
        onSuccess();
      }
      await refreshAll();
    } catch (error) {
      setMessage(`${label} failed: ${error.message}`);
    }
  }

  return (
    <div className="operator-layout">
      <section className="operator-machine-column">
        <Panel title="Machine Panel">
          <div className="machine-visual">HAAS VF2</div>
          <p>
            <strong>Machine:</strong> {MACHINE_ID}
          </p>
          <p>
            <strong>State:</strong> <MachineStatusBadge state={currentState} />
          </p>
          <p>
            <strong>Active Operator:</strong> {operatorSession?.operator_name || "-"}
          </p>
          <div className="metric-grid">
            <div>
              <small>Produced</small>
              <div>{machineState.produced_count}</div>
            </div>
            <div>
              <small>Target</small>
              <div>{activeJob?.target_quantity ?? "-"}</div>
            </div>
            <div>
              <small>Scrap</small>
              <div>{machineState.scrap_count}</div>
            </div>
          </div>
          <p className="message">{message}</p>
        </Panel>

        <Panel title="Machine Controls">
          <div className="stack">
            <input
              placeholder="Control note (optional)"
              value={controlNote}
              onChange={(e) => setControlNote(e.target.value)}
            />
            <div className="form-row">
              <select value={pauseReason} onChange={(e) => setPauseReason(e.target.value)}>
                {PAUSE_REASONS.map((reason) => (
                  <option key={reason} value={reason}>
                    Pause: {reason}
                  </option>
                ))}
              </select>
              <select value={alarmReason} onChange={(e) => setAlarmReason(e.target.value)}>
                {ALARM_REASONS.map((reason) => (
                  <option key={reason} value={reason}>
                    Alarm: {reason}
                  </option>
                ))}
              </select>
            </div>
            <div className="button-grid">
              <button type="button" disabled={!canStartSetup} onClick={() => runAction("Start Setup", () => api.startSetup(operatorId))}>
                Start Setup
              </button>
              <button
                type="button"
                disabled={!canConfirmSetup}
                onClick={() => runAction("Confirm Setup", () => api.confirmSetup(operatorId))}
              >
                Confirm Setup Ready
              </button>
              <button type="button" disabled={!canStartCycle} onClick={() => runAction("Cycle Start", () => api.startCycle(operatorId))}>
                Cycle Start
              </button>
              <button
                type="button"
                disabled={!canPauseCycle}
                onClick={() => runAction("Pause", () => api.pauseCycle(operatorId, pauseReason, controlNote))}
              >
                Pause
              </button>
              <button
                type="button"
                disabled={!canResumeCycle}
                onClick={() => runAction("Resume", () => api.resumeCycle(operatorId, controlNote))}
              >
                Resume
              </button>
              <button
                type="button"
                disabled={!canTriggerAlarm}
                onClick={() => runAction("Trigger Alarm", () => api.triggerAlarm(operatorId, alarmReason, controlNote))}
              >
                Trigger Alarm
              </button>
              <button
                type="button"
                disabled={!canClearAlarm}
                onClick={() => runAction("Clear Alarm", () => api.clearAlarm(operatorId, controlNote))}
              >
                Clear Alarm
              </button>
              <button
                type="button"
                disabled={!canCompletePart}
                onClick={() => runAction("Part Complete", () => api.completeCycle(operatorId))}
              >
                Part Complete
              </button>
              <button
                type="button"
                disabled={!canFinishJob}
                onClick={() => runAction("Finish Job", () => api.finishJob(operatorId, controlNote))}
              >
                Finish Job
              </button>
            </div>
          </div>
        </Panel>
      </section>

      <section className="operator-work-column">
        <Panel title="Operator Work Area">
          <p>
            <strong>Active job:</strong> {activeJob ? `${activeJob.job_id} - ${activeJob.part_name}` : "-"}
          </p>
          <p>
            <strong>Drawing file:</strong> {activeJob?.drawing_file || "-"}
          </p>
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
              disabled={!canSelectJob || !selectedJob}
              onClick={() => runAction("Select Job", () => api.selectJob(selectedJob, operatorId))}
            >
              Select Job
            </button>
          </div>
        </Panel>

        <Panel title="Notes">
          <div className="stack">
            <textarea
              rows={4}
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              placeholder="Operator note"
            />
            <button
              type="button"
              disabled={!canAddNote || !noteText.trim()}
              onClick={() =>
                runAction(
                  "Save Note",
                  () => api.addNote(noteText, operatorId),
                  () => setNoteText(""),
                )
              }
            >
              Save Note
            </button>
          </div>
        </Panel>

        <Panel title="Scrap Reporting">
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
          </div>
          <div className="form-row">
            <input placeholder="Scrap note" value={scrapNote} onChange={(e) => setScrapNote(e.target.value)} />
            <button
              type="button"
              disabled={!canReportScrap || scrapQty <= 0}
              onClick={() =>
                runAction(
                  "Report Scrap",
                  () => api.reportScrap(scrapQty, scrapReason, scrapNote, operatorId),
                  () => setScrapNote(""),
                )
              }
            >
              Submit Scrap
            </button>
          </div>
        </Panel>

        <EventTimeline events={events} />
      </section>
    </div>
  );
}