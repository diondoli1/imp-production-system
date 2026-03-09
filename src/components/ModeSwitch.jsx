import React from "react";
export default function ModeSwitch({ mode, onChange }) {
  return (
    <div className="mode-switch">
      <button
        className={mode === "operator" ? "active" : ""}
        onClick={() => onChange("operator")}
        type="button"
      >
        Operator Interface
      </button>
      <button
        className={mode === "dashboard" ? "active" : ""}
        onClick={() => onChange("dashboard")}
        type="button"
      >
        Supervisor Dashboard
      </button>
    </div>
  );
}
