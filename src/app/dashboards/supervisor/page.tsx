"use client";
import { PageShell } from "@/components/PageShell";
import { DashboardRenderer } from "@/lib/dashboards/widgets";
import { supervisor } from "@/lib/dashboards/dashboard-schema";
export default function SupervisorDashboard() {
  return (
    <PageShell title="Supervisor Dashboard" requireAuth={true}>
      <DashboardRenderer schema={supervisor} title={supervisor.title} description={supervisor.description} />
    </PageShell>
  );
}
