import { WorkbenchLayout } from '@/components/workbench/WorkbenchLayout';
import type { ReactNode } from 'react';

export default function WorkbenchPageLayout({ children }: { children: ReactNode }) {
  return <WorkbenchLayout>{children}</WorkbenchLayout>;
}
