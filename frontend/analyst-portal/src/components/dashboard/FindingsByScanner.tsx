'use client';

import { Card, CardHeader } from '@/components/common/Card';

interface FindingsByScannerProps {
  scannerCounts: Record<string, number>;
}

const scannerLabels: Record<string, string> = {
  burp_suite: 'Burp Suite',
  nuclei: 'Nuclei',
  fortify: 'Fortify',
  tenable: 'Tenable',
  mobsf: 'MobSF',
  nmap: 'Nmap',
  scoutsuite: 'ScoutSuite',
  trivy: 'Trivy',
  zap: 'ZAP',
};

export function FindingsByScanner({ scannerCounts }: FindingsByScannerProps) {
  const entries = Object.entries(scannerCounts).sort(([, a], [, b]) => b - a);
  const max = entries.length > 0 ? entries[0][1] : 1;

  return (
    <Card>
      <CardHeader title="Findings by Scanner" />
      <div className="mt-4 space-y-2">
        {entries.map(([scanner, count]) => (
          <div key={scanner} className="flex items-center gap-3">
            <span className="w-24 text-sm text-gray-700">{scannerLabels[scanner] || scanner}</span>
            <div className="flex-1">
              <div className="h-5 rounded bg-gray-100">
                <div
                  className="flex h-5 items-center rounded bg-indigo-500 px-2 text-xs font-medium text-white transition-all"
                  style={{ width: `${(count / max) * 100}%`, minWidth: '2rem' }}
                >
                  {count}
                </div>
              </div>
            </div>
          </div>
        ))}
        {entries.length === 0 && (
          <p className="text-sm text-gray-500">No scanner data available</p>
        )}
      </div>
    </Card>
  );
}
