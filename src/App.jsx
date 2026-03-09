import React from "react";
import { useEffect, useState } from "react";

import ModeSwitch from "./components/ModeSwitch";
import OperatorPage from "./pages/OperatorPage";
import DashboardPage from "./pages/DashboardPage";
import { api } from "./services/api";
import { connectWebSocket } from "./services/ws";

const DEFAULT_MACHINE_STATE = {
  machine_id: "HAAS_VF2_01",
  current_state: "IDLE",
  active_job_id: null,
  active_operator_id: null,
  produced_count: 0,
  scrap_count: 0,
  updated_at: null,
};

export default function App() {
  const [mode, setMode] = useState("operator");
  const [machineState, setMachineState] = useState(DEFAULT_MACHINE_STATE);
  const [jobs, setJobs] = useState([]);
  const [events, setEvents] = useState([]);
  const [operatorSession, setOperatorSession] = useState(null);
  const [wsStatus, setWsStatus] = useState("disconnected");

  async function refreshAll() {
    const [state, jobList, eventList] = await Promise.all([
      api.getMachineState(),
      api.getJobs(),
      api.getMachineEvents(50),
    ]);
    setMachineState(state);
    setJobs(jobList);
    setEvents(eventList);
  }

  useEffect(() => {
    refreshAll().catch(() => {});
  }, []);

  useEffect(() => {
    const disconnect = connectWebSocket(
      (payload) => {
        if (payload.type === "machine_state_updated") {
          setMachineState((prev) => ({ ...prev, ...payload }));
        }
        if (payload.type === "production_count_updated") {
          setMachineState((prev) => ({ ...prev, produced_count: payload.produced_count }));
        }
        if (payload.type === "scrap_count_updated") {
          setMachineState((prev) => ({ ...prev, scrap_count: payload.scrap_count }));
        }
        if (payload.type === "event_created" && payload.event) {
          setEvents((prev) => [payload.event, ...prev].slice(0, 50));
        }
        if (payload.type === "ai_report_created") {
          setEvents((prev) => [
            {
              event_id: Date.now(),
              timestamp: new Date().toISOString(),
              event_type: "ai_report_created",
              machine_state: machineState.current_state,
              job_id: payload.report?.job_id || null,
              operator_id: payload.report?.operator_id || null,
              reason_code: null,
              details: JSON.stringify(payload.report || {}),
            },
            ...prev,
          ]);
        }
      },
      setWsStatus,
    );
    return disconnect;
  }, [machineState.current_state]);

  return (
    <div className="app-shell">
      <header className="top-bar">
        <h1>IMP CNC Production Tracking Prototype</h1>
      </header>

      <ModeSwitch mode={mode} onChange={setMode} />

      {mode === "operator" ? (
        <OperatorPage
          machineState={machineState}
          jobs={jobs}
          events={events}
          operatorSession={operatorSession}
          setOperatorSession={setOperatorSession}
          refreshAll={refreshAll}
        />
      ) : (
        <DashboardPage machineState={machineState} events={events} wsStatus={wsStatus} />
      )}
    </div>
  );
}
