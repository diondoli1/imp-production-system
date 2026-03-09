import React from "react";
import EventTimeline from "../components/EventTimeline";
import MachineStatusBadge from "../components/MachineStatusBadge";
import Panel from "../components/Panel";
import { MACHINE_ID } from "../constants";
import { api } from "../services/api";

export default function DashboardPage({ machineState, events, wsStatus }) {
  const runningEvents = events.filter((event) => event.machine_state === "RUNNING").length;
  const alarmEvents = events.filter((event) => event.event_type === "alarm_triggered").length;

  return (
    <div className="page-grid">
      <Panel title="1) Machine Status Panel">
        <p>
          <strong>Machine:</strong> {MACHINE_ID}
        </p>
        <p>
          <strong>State:</strong> <MachineStatusBadge state={machineState.current_state} />
        </p>
        <p>
          <strong>Active Job:</strong> {machineState.active_job_id || "-"}
        </p>
        <p>
          <strong>Active Operator:</strong> {machineState.active_operator_id || "-"}
        </p>
        <p>
          <strong>WebSocket:</strong> {wsStatus}
        </p>
      </Panel>

      <Panel title="2) Production Metrics">
        <p>Produced Count: {machineState.produced_count}</p>
        <p>Scrap Count: {machineState.scrap_count}</p>
      </Panel>

      <EventTimeline events={events} />

      <Panel title="4) Runtime Metrics">
        <p>Recent RUNNING state entries: {runningEvents}</p>
        <p>Recent alarm triggers: {alarmEvents}</p>
        <p>Last update: {machineState.updated_at ? new Date(machineState.updated_at).toLocaleString() : "-"}</p>
      </Panel>

      <Panel title="5) AI Insight Panel">
        <p>Generate deterministic AI insights from backend history:</p>
        <div className="button-grid">
          <button type="button" onClick={() => api.getAIPlaceholder()}>
            Trigger Placeholder AI Report
          </button>
        </div>
      </Panel>
    </div>
  );
}
