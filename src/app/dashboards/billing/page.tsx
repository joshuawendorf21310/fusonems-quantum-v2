"use client";
import { PageShell } from "@/components/PageShell";
import { DashboardRenderer } from "@/lib/dashboards/widgets";
import { billing } from "@/lib/dashboards/dashboard-schema";
export default function BillingDashboard() {
  return (
    <PageShell title="Billing Dashboard" requireAuth={true}>
      <DashboardRenderer schema={billing} title={billing.title} description={billing.description} />
    </PageShell>
  );
}
