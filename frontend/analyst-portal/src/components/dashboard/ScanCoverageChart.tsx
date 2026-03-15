'use client';

import { Card, CardHeader } from '@/components/common/Card';
import type { ScanCoverage } from '@/types/engagement';

interface ScanCoverageChartProps {
  coverage: ScanCoverage[];
}

export function ScanCoverageChart({ coverage }: ScanCoverageChartProps) {
  return (
    <Card>
      <CardHeader title="Scan Coverage" />
      <div className="mt-4 space-y-3">
        {coverage.map((item) => (
          <div key={item.assetType}>
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-gray-700">{item.assetType}</span>
              <span className="text-gray-500">
                {item.scannedAssets}/{item.totalAssets} ({item.coveragePercent}%)
              </span>
            </div>
            <div className="mt-1 h-2 w-full rounded-full bg-gray-200">
              <div
                className="h-2 rounded-full bg-blue-600 transition-all"
                style={{ width: `${item.coveragePercent}%` }}
              />
            </div>
          </div>
        ))}
        {coverage.length === 0 && (
          <p className="text-sm text-gray-500">No scan data available</p>
        )}
      </div>
    </Card>
  );
}
