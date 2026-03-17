import { priorityClass } from "../utils/formatters";

export default function ApprovalsTable({ approvals }) {
  if (!approvals?.length) return <div className="hud-card"><h2 className="card-title">PENDING APPROVALS</h2><p className="empty-msg">No pending approvals</p></div>;

  return (
    <div className="hud-card">
      <h2 className="card-title">PENDING APPROVALS <span className="badge badge-accent">{approvals.length}</span></h2>
      <div className="table-wrap">
        <table className="hud-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Priority</th>
              <th>Requested</th>
              <th>Domain</th>
              <th>File</th>
            </tr>
          </thead>
          <tbody>
            {approvals.map((a) => (
              <tr key={a.filename}>
                <td>{a.action_type}</td>
                <td><span className={`badge ${priorityClass(a.priority)}`}>{a.priority}</span></td>
                <td>{a.requested}</td>
                <td><span className="badge badge-domain">{a.domain}</span></td>
                <td className="cell-filename">{a.filename}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
