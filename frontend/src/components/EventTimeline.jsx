import React from "react";
import Panel from "./Panel";

export default function EventTimeline({ events }) {
  return (
    <Panel title="Event Timeline">
      <ul className="timeline-list">
        {events.map((event) => (
          <li key={event.event_id} className="timeline-item">
            <strong>{event.event_type}</strong>
            <span>{new Date(event.timestamp).toLocaleString()}</span>
            <small>
              state={event.machine_state} job={event.job_id || "-"} op={event.operator_id || "-"}
            </small>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
