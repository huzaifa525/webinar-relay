import { redirect } from 'next/navigation';

export const dynamic = 'force-dynamic';

// Asbaaq module temporarily disabled
export default function WebinarPage() {
  redirect('/');
}
