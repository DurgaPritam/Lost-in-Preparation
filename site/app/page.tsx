import { Home } from '@/features/home/Home';
import { getHome } from '@/lib/data/site';

export default function Page() {
  const d = getHome();
  return <Home coverage={d.coverage} confidences={d.confidences} gap={d.gap} />;
}
