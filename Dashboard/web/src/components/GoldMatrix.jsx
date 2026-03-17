const GOLD_ITEMS = [
  { id: "G1", name: "CEO Briefing", pass: true },
  { id: "G2", name: "Error Recovery", pass: true },
  { id: "G3", name: "Ralph Loop", pass: true },
  { id: "G4", name: "Additional MCPs", pass: true },
  { id: "G5", name: "Cross-Domain", pass: true },
  { id: "G6", name: "Odoo Accounting", pass: true },
  { id: "G7", name: "Social Media", pass: true },
];

export default function GoldMatrix() {
  return (
    <div className="hud-card">
      <h2 className="card-title">GOLD VERIFICATION MATRIX</h2>
      <div className="gold-grid">
        {GOLD_ITEMS.map((g) => (
          <div key={g.id} className={`gold-cell ${g.pass ? "gold-pass" : "gold-fail"}`}>
            <span className="gold-icon">{g.pass ? "\u2713" : "\u2717"}</span>
            <span className="gold-id">{g.id}</span>
            <span className="gold-name">{g.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
