import React, { useEffect, useState } from "react";

import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import OperatorPage from "./pages/OperatorPage";
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

const ALLOWED_PATHS = new Set(["/login", "/operator", "/supervisor"]);

function normalizePath(pathname) {
  if (!pathname || pathname === "/") {
    return "/login";
  }
  return pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;
}

export default function App() {
  const [path, setPath] = useState(() => normalizePath(window.location.pathname));
  const [machineState, setMachineState] = useState(DEFAULT_MACHINE_STATE);
  const [jobs, setJobs] = useState([]);
  const [events, setEvents] = useState([]);
  const [session, setSession] = useState(null);
  const [operatorSession, setOperatorSession] = useState(null);
  const [wsStatus, setWsStatus] = useState("disconnected");

  function navigate(nextPath, replace = false) {
    const target = normalizePath(nextPath);
    if (replace) {
      window.history.replaceState({}, "", target);
    } else {
      window.history.pushState({}, "", target);
    }
    setPath(target);
  }

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

  async function handleLogin(name, pin) {
    const result = await api.loginApp(name, pin);
    const payload = result.data || {};
    if (!payload.role || !payload.redirect_path) {
      throw new Error("Invalid login response from backend");
    }

    setSession(payload);
    if (payload.role === "OPERATOR") {
      setOperatorSession({
        operator_id: payload.operator_id,
        operator_name: payload.operator_name || payload.name,
      });
    } else {
      setOperatorSession(null);
    }

    navigate(payload.redirect_path);
    await refreshAll();
  }

  async function handleLogout() {
    if (operatorSession?.operator_id) {
      try {
        await api.logoutOperator(operatorSession.operator_id);
      } catch {
        // Keep logout UX resilient when operator session is already cleared server-side.
      }
    }
    setSession(null);
    setOperatorSession(null);
    navigate("/login", true);
    await refreshAll();
  }

  useEffect(() => {
    const onPopState = () => {
      setPath(normalizePath(window.location.pathname));
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    if (!ALLOWED_PATHS.has(path)) {
      navigate("/login", true);
      return;
    }

    if (path === "/operator" && session?.role !== "OPERATOR") {
      navigate("/login", true);
      return;
    }

    if (path === "/supervisor" && session?.role !== "SUPERVISOR") {
      navigate("/login", true);
    }
  }, [path, session]);

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
        <div className="form-row">
          <span>{session ? `${session.name} (${session.role})` : "Not logged in"}</span>
          {session ? (
            <button type="button" onClick={handleLogout}>
              Logout
            </button>
          ) : null}
        </div>
      </header>

      {path === "/login" ? (
        <LoginPage onLogin={handleLogin} />
      ) : null}

      {path === "/operator" ? (
        <OperatorPage
          machineState={machineState}
          jobs={jobs}
          events={events}
          operatorSession={operatorSession}
          setOperatorSession={setOperatorSession}
          refreshAll={refreshAll}
        />
      ) : null}

      {path === "/supervisor" ? (
        <DashboardPage machineState={machineState} events={events} wsStatus={wsStatus} refreshAll={refreshAll} />
      ) : null}
    </div>
  );
}
