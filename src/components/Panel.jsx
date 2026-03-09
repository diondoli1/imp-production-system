import React from "react";
export default function Panel({ title, children, actions }) {
  return (
    <section className="panel">
      <header className="panel-header">
        <h3>{title}</h3>
        <div>{actions}</div>
      </header>
      <div className="panel-body">{children}</div>
    </section>
  );
}
