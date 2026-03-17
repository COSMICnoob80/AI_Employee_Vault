import { useState } from "react";

export default function BriefingPreview({ briefing }) {
  const [expanded, setExpanded] = useState(false);

  if (!briefing?.executive_summary) return null;

  const summary = briefing.executive_summary;
  const truncated = summary.length > 300 ? summary.slice(0, 300) + "..." : summary;

  return (
    <div className="hud-card">
      <h2 className="card-title">CEO BRIEFING</h2>
      <div className="briefing-meta">
        <span>Week: {briefing.week}</span>
        <span>Generated: {briefing.generated}</span>
      </div>
      <div className="briefing-body">
        {expanded ? summary : truncated}
      </div>
      {summary.length > 300 && (
        <button className="btn-expand" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Collapse" : "Expand"}
        </button>
      )}
    </div>
  );
}
