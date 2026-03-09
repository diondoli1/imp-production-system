import React from "react";
export default function MachineStatusBadge({ state }) {
  const normalized = state || "IDLE";
  return <span className={`state-badge state-${normalized}`}>{normalized}</span>;
}
