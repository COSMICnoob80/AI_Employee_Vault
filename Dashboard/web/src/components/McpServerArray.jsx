export default function McpServerArray({ servers }) {
  if (!servers?.length) return null;

  return (
    <div className="hud-card">
      <h2 className="card-title">MCP SERVERS</h2>
      <div className="mcp-grid">
        {servers.map((s) => (
          <div key={s.name} className="mcp-server-card">
            <span className="status-dot" style={{ background: "var(--success)", boxShadow: "0 0 6px var(--success)" }} />
            <div className="mcp-info">
              <span className="mcp-name">{s.name}</span>
              <span className="mcp-tools">{s.tool_count} tools</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
