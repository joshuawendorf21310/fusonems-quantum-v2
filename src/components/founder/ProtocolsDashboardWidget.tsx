import ProtocolImportWidget from "../admin/ProtocolImportWidget";

export function ProtocolsDashboardWidget() {
  return (
    <section className="panel">
      <header>
        <h3>Protocols Management</h3>
        <p className="muted-text">Import, review, and manage agency protocols.</p>
      </header>
      <ProtocolImportWidget />
      {/* TODO: Add protocol list, review/approval, search, tagging, in-app viewer */}
    </section>
  );
}
