import { NextRequest, NextResponse } from 'next/server';

interface SearchResult {
  module: string;
  id: string;
  title: string;
  subtitle: string;
  url: string;
}

// Mock data for demonstration - replace with actual database queries
const mockData: SearchResult[] = [
  // ePCR
  { module: "ePCR", id: "1", title: "PCR-2025-001", subtitle: "John Doe - Chest Pain", url: "/epcr/1" },
  { module: "ePCR", id: "2", title: "PCR-2025-002", subtitle: "Jane Smith - MVA", url: "/epcr/2" },
  { module: "ePCR", id: "3", title: "Pending PCR Review", subtitle: "5 reports awaiting approval", url: "/epcr" },

  // CAD
  { module: "CAD", id: "1", title: "INC-2025-1124", subtitle: "Cardiac Arrest - 123 Main St", url: "/cad/incidents/1124" },
  { module: "CAD", id: "2", title: "Structure Fire Summary", subtitle: "7th Battalion • Station 4", url: "/cad/incidents" },

  // Fire
  { module: "Fire", id: "1", title: "Fire RMS Executive", subtitle: "Review hydrants, inspections, CRR", url: "/fire/rms" },

  // Fleet
  { module: "Fleet", id: "1", title: "Unit M-101", subtitle: "Available - Station 1", url: "/fleet/vehicles/M-101" },
  { module: "Fleet", id: "2", title: "Unit M-102", subtitle: "On Scene - Main St", url: "/fleet/vehicles/M-102" },
  { module: "Fleet", id: "3", title: "Fleet Inspections Due", subtitle: "4 units need checks this week", url: "/fleet/inspections" },

  // Patients
  { module: "Patients", id: "1", title: "John Doe", subtitle: "Patient Portal • Balance $450.00", url: "/portals/patient/dashboard" },
  { module: "Patients", id: "2", title: "Update Insurance", subtitle: "Patient profile task", url: "/portals/patient/profile" },
  { module: "Patients", id: "3", title: "View Bill", subtitle: "Billing snapshot", url: "/portals/patient/bills" },

  // Bills
  { module: "Bills", id: "1", title: "Denied Claim #2025-011", subtitle: "Billing denial workflow", url: "/billing/denial-workflow" },
  { module: "Bills", id: "2", title: "Batch Submit", subtitle: "32 claims queued", url: "/billing/batch-submit" },

  // Personnel
  { module: "Personnel", id: "1", title: "Michael Brown", subtitle: "Paramedic • Station 1", url: "/hr/personnel/1" },
  { module: "Personnel", id: "2", title: "Expiring Certifications", subtitle: "5 certifications need renewal", url: "/hr/certifications" },

  // Scheduling
  { module: "Scheduling", id: "1", title: "Crew Forecast", subtitle: "Predictive pairing for next week", url: "/scheduling/predictive" },
  { module: "Scheduling", id: "2", title: "Today’s Schedule", subtitle: "15 shifts scheduled", url: "/scheduling" },

  // Compliance & Analytics
  { module: "Compliance", id: "1", title: "CMS Audit Preferences", subtitle: "Founder compliance workspace", url: "/founder/compliance/cms" },
  { module: "Reports", id: "1", title: "Founder Reports", subtitle: "Natural language report writer", url: "/founder/reports" },
  { module: "Reports", id: "2", title: "Document Studio", subtitle: "Report templates & exports", url: "/founder/documents" },
]

function fuzzyMatch(text: string, query: string): boolean {
  const normalizedText = text.toLowerCase();
  const normalizedQuery = query.toLowerCase();
  
  // Exact match
  if (normalizedText.includes(normalizedQuery)) {
    return true;
  }
  
  // Fuzzy match - check if all query characters appear in order
  let textIndex = 0;
  for (const char of normalizedQuery) {
    textIndex = normalizedText.indexOf(char, textIndex);
    if (textIndex === -1) {
      return false;
    }
    textIndex++;
  }
  
  return true;
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.get('q');
    const moduleFilter = searchParams.get('module');

    if (!query || query.trim().length === 0) {
      return NextResponse.json([]);
    }

    // Filter results based on query and module
    let results = mockData.filter((item) => {
      const matchesQuery =
        fuzzyMatch(item.title, query) ||
        fuzzyMatch(item.subtitle, query) ||
        fuzzyMatch(item.module, query);

      const matchesModule =
        !moduleFilter ||
        moduleFilter === 'All' ||
        item.module.toLowerCase() === moduleFilter.toLowerCase();

      return matchesQuery && matchesModule;
    });

    // Sort by relevance (exact matches first)
    results.sort((a, b) => {
      const aExact = a.title.toLowerCase().includes(query.toLowerCase()) ? 1 : 0;
      const bExact = b.title.toLowerCase().includes(query.toLowerCase()) ? 1 : 0;
      return bExact - aExact;
    });

    return NextResponse.json(results);
  } catch (error) {
    console.error('Global search error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
