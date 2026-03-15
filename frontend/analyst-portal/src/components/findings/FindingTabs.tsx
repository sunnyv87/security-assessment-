'use client';

import * as Tabs from '@radix-ui/react-tabs';
import { DetailsTab } from './DetailsTab';
import { ValidationPanel } from '@/components/validation/ValidationPanel';
import { PocRecorder } from '@/components/poc/PocRecorder';
import { RemediationGuidance } from '@/components/remediation/RemediationGuidance';
import type { Finding } from '@/types/finding';

interface FindingTabsProps {
  finding: Finding;
}

const tabs = [
  { value: 'details', label: 'Details' },
  { value: 'validation', label: 'Validation' },
  { value: 'poc', label: 'PoC' },
  { value: 'remediation', label: 'Remediation' },
  { value: 'history', label: 'History' },
];

export function FindingTabs({ finding }: FindingTabsProps) {
  return (
    <Tabs.Root defaultValue="details">
      <Tabs.List className="flex border-b border-gray-200">
        {tabs.map((tab) => (
          <Tabs.Trigger
            key={tab.value}
            value={tab.value}
            className="border-b-2 border-transparent px-4 py-2.5 text-sm font-medium text-gray-500 transition-colors hover:text-gray-700 data-[state=active]:border-blue-600 data-[state=active]:text-blue-600"
          >
            {tab.label}
          </Tabs.Trigger>
        ))}
      </Tabs.List>

      <div className="mt-6">
        <Tabs.Content value="details">
          <DetailsTab finding={finding} />
        </Tabs.Content>

        <Tabs.Content value="validation">
          <ValidationPanel findingId={finding.id} />
        </Tabs.Content>

        <Tabs.Content value="poc">
          <PocRecorder findingId={finding.id} />
        </Tabs.Content>

        <Tabs.Content value="remediation">
          <RemediationGuidance findingId={finding.id} />
        </Tabs.Content>

        <Tabs.Content value="history">
          <div className="text-sm text-gray-500">Audit history timeline (coming soon)</div>
        </Tabs.Content>
      </div>
    </Tabs.Root>
  );
}
