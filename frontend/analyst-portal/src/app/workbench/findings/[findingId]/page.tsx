import { FindingDetailPanel } from '@/components/findings/FindingDetailPanel';

interface FindingPageProps {
  params: { findingId: string };
}

export default function FindingPage({ params }: FindingPageProps) {
  return <FindingDetailPanel findingId={params.findingId} />;
}
