'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { DashboardProvider } from '@/contexts/DashboardContext';
import { Sidebar } from '@/components/layout/Sidebar';
import { Topbar } from '@/components/layout/Topbar';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) router.replace('/login');
  }, [user, isLoading, router]);

  if (isLoading || !user) return null;

  return (
    <DashboardProvider>
      <div className="app">
        <Sidebar />
        <div className="main">
          <Topbar onMenuClick={() => setMobileOpen(!mobileOpen)} />
          <main className="content">
            {children}
          </main>
        </div>
      </div>
    </DashboardProvider>
  );
}
