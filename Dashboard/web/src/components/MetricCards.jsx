export default function MetricCards({ mcpCount, components, goldPassed }) {
  const watcherCount = components?.filter((c) => c.name?.toLowerCase().includes("watcher")).length || 0;

  const cards = [
    { label: "MCP SERVERS", value: mcpCount ?? "—" },
    { label: "SKILLS", value: 15 },
    { label: "ACTIVE WATCHERS", value: watcherCount },
    { label: "GOLD CHECKS", value: `${goldPassed}/7` },
  ];

  return (
    <div className="metric-cards">
      {cards.map((c) => (
        <div key={c.label} className="hud-card metric-card">
          <span className="metric-value">{c.value}</span>
          <span className="metric-label">{c.label}</span>
        </div>
      ))}
    </div>
  );
}
