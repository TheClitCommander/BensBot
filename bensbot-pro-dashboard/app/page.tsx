import { redirect } from 'next/navigation';

export default function Home() {
  // Redirect to dashboard from the root
  redirect('/dashboard');
}
