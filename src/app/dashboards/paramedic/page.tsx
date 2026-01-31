"use client";
import { PageShell } from "@/components/PageShell";
import { DashboardRenderer } from "@/lib/dashboards/widgets";
import { paramedic } from "@/lib/dashboards/dashboard-schema";
export default function ParamedicDashboard() {
  return (
    <PageShell title="Paramedic Dashboard" requireAuth={true}>
      <DashboardRenderer schema={paramedic} title={paramedic.title} description={paramedic.description} />
    </PageShell>
  );
}
