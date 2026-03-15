import { PocRecorder } from '@/components/poc/PocRecorder';

interface PocPageProps {
  params: { findingId: string };
}

export default function PocPage({ params }: PocPageProps) {
  return <PocRecorder findingId={params.findingId} />;
}
