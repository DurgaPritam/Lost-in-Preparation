import { Landing } from '@/features/landing/Landing';
import { getLanding } from '@/lib/data/site';
import { loadEngineModel } from '@/lib/data/load';

export default function Page() {
  return <Landing {...getLanding()} model={loadEngineModel()} />;
}
