/**
 * Portals layout: no homepage hero/orbs, clean dark background, content on top.
 * Ensures /portals never shows the homepage decorative background or a stray full-page graphic.
 */
export default function PortalsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div
      className="min-h-screen bg-[#0a0a0a] relative"
      style={{ isolation: "isolate" }}
    >
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}
