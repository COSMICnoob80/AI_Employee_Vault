import { useState, useEffect } from "react";

export default function HeaderBar({ components }) {
  const [clock, setClock] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const allOk = components?.every((c) => c.status === "active");
  const hasError = components?.some((c) => c.status === "error");
  const pulseColor = hasError ? "var(--alert)" : allOk ? "var(--success)" : "var(--warning)";

  return (
    <header className="header-bar">
      <div className="scan-line" />
      <div className="header-content">
        <div className="header-left">
          <span className="pulse-dot" style={{ background: pulseColor, boxShadow: `0 0 8px ${pulseColor}` }} />
          <h1 className="header-title">AEWACS COMMAND CENTER</h1>
        </div>
        <div className="header-right">
          <span className="header-clock">
            {clock.toLocaleTimeString("en-US", { hour12: false })}
          </span>
          <span className="header-date">
            {clock.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })}
          </span>
        </div>
      </div>
    </header>
  );
}
