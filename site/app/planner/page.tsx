import type { Metadata } from 'next';
import { LabPlanner } from '@/features/planner/LabPlanner';
import { getPlanner } from '@/lib/data/site';

export const metadata: Metadata = { title: 'Lab Planner' };
export default function Page() {
  return <LabPlanner {...getPlanner()} />;
}
