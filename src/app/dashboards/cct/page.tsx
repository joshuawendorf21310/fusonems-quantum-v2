"use client";
import { PageShell } from "@/components/PageShell";
import { DashboardRenderer } from "@/lib/dashboards/widgets";
import { paramedic } from "@/lib/dashboards/dashboard-schema";
export default function CctDashboard() {
  const cctSchema = { ...paramedic, title: "CCT Dashboard", description: "Flight crew metrics" };
  return (
    <PageShell title="Critical Care Transport Dashboard" requireAuth={true}>
      <DashboardRenderer schema={cctSchema} title={cctSchema.title} description={cctSchema.description} />
    </PageShell>
  );
}
