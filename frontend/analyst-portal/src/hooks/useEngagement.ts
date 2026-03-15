import { useQuery } from '@tanstack/react-query';
import { fetchEngagements, fetchScanCoverage } from '@/lib/api-client';
import { useWorkbenchStore } from '@/stores/workbenchStore';
import { useEffect } from 'react';

export function useEngagement(engagementId: string | null) {
  const setEngagements = useWorkbenchStore((s) => s.setEngagements);

  const engagementsQuery = useQuery({
    queryKey: ['engagements'],
    queryFn: fetchEngagements,
  });

  useEffect(() => {
    if (engagementsQuery.data) {
      setEngagements(engagementsQuery.data);
    }
  }, [engagementsQuery.data, setEngagements]);

  const coverageQuery = useQuery({
    queryKey: ['scan-coverage', engagementId],
    queryFn: () => fetchScanCoverage(engagementId!),
    enabled: !!engagementId,
  });

  return {
    engagements: engagementsQuery.data,
    scanCoverage: coverageQuery.data,
  };
}
