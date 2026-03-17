const TIERS = [
  { name: "Bronze", done: true, items: "3/3" },
  { name: "Silver", done: true, items: "8/8" },
  { name: "Gold", done: true, items: "7/7" },
  { name: "Platinum", done: false, items: "0/?" },
];

export default function TierProgress() {
  return (
    <div className="hud-card tier-progress">
      <h2 className="card-title">TIER PROGRESS</h2>
      <div className="tier-bar">
        {TIERS.map((t) => (
          <div key={t.name} className={`tier-segment ${t.done ? "tier-done" : "tier-pending"}`}>
            <span className="tier-label">{t.name}</span>
            <span className="tier-count">{t.items}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
