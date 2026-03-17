import { statusColor } from "../utils/formatters";

export default function StatusGrid({ components }) {
  if (!components?.length) return null;

  return (
    <div className="hud-card">
      <h2 className="card-title">COMPONENT STATUS</h2>
      <div className="status-grid">
        {components.map((c) => (
          <div key={c.name} className="status-cell">
            <span className="status-dot" style={{ background: statusColor(c.status), boxShadow: `0 0 6px ${statusColor(c.status)}` }} />
            <div className="status-info">
              <span className="status-name">{c.name}</span>
              <span className="status-activity">{c.last_activity}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
