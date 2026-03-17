import usePolling from "./hooks/usePolling";
import { fetchStatus, fetchTasks, fetchApprovals, fetchBriefing, fetchOdooSummary, fetchAudit, fetchMcp } from "./utils/api";

import HeaderBar from "./components/HeaderBar";
import TierProgress from "./components/TierProgress";
import MetricCards from "./components/MetricCards";
import StatusGrid from "./components/StatusGrid";
import McpServerArray from "./components/McpServerArray";
import OdooPanel from "./components/OdooPanel";
import ApprovalsTable from "./components/ApprovalsTable";
import GoldMatrix from "./components/GoldMatrix";
import BriefingPreview from "./components/BriefingPreview";
import AuditTail from "./components/AuditTail";

export default function App() {
  const { data: status } = usePolling(fetchStatus, 30000);
  const { data: tasks } = usePolling(fetchTasks, 60000);
  const { data: approvals } = usePolling(fetchApprovals, 60000);
  const { data: briefing } = usePolling(fetchBriefing, 300000);
  const { data: odooSummary } = usePolling(fetchOdooSummary, 300000);
  const { data: audit } = usePolling(fetchAudit, 30000);
  const { data: mcp } = usePolling(fetchMcp, 300000);

  return (
    <div className="app">
      <HeaderBar components={status?.components} />
      <main className="main-grid">
        <TierProgress />
        <MetricCards
          mcpCount={mcp?.count}
          components={status?.components}
          goldPassed={7}
        />
        <StatusGrid components={status?.components} />
        <McpServerArray servers={mcp?.servers} />
        <div className="two-col">
          <OdooPanel summary={odooSummary} />
          <ApprovalsTable approvals={approvals?.approvals} />
        </div>
        <GoldMatrix />
        <BriefingPreview briefing={briefing} />
        <AuditTail entries={audit?.entries} />
        <footer className="footer">
          <span>AEWACS v1.0 &middot; AI Employee Vault</span>
          <span>Tasks: {tasks?.count ?? "—"} &middot; Approvals: {approvals?.count ?? "—"}</span>
        </footer>
      </main>
    </div>
  );
}
