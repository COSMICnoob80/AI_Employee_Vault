import { formatRelativeTime, statusColor } from "../utils/formatters";

export default function AuditTail({ entries }) {
  if (!entries?.length) return null;

  return (
    <div className="hud-card">
      <h2 className="card-title">AUDIT LOG</h2>
      <div className="table-wrap">
        <table className="hud-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Event</th>
              <th>Source</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e, i) => (
              <tr key={i}>
                <td className="cell-mono">{formatRelativeTime(e.ts)}</td>
                <td>{e.event}</td>
                <td>{e.source}</td>
                <td>
                  <span className="badge" style={{ background: statusColor(e.status), color: "#0a0e14" }}>
                    {e.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
