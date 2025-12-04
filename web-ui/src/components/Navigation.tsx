'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/components/AuthProvider';

export default function Navigation() {
  const pathname = usePathname();
  const { user, logout, isAuthenticated } = useAuth();

  const navItems = [
    { href: '/', label: 'Dashboard' },
    { href: '/clusters', label: 'Clusters' },
    { href: '/security', label: 'Security' },
    { href: '/audit', label: 'Audit Logs' },
    { href: '/guidance', label: 'API Guidance' },
    { href: '/health', label: 'Health' },
    { href: '/docs', label: 'Documentation' },
  ];

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center">
            <Link href="/" className="text-xl font-bold text-gray-900 hover:text-gray-700">
              Nexus Dashboard MCP Server
            </Link>
          </div>
          <div className="flex items-center space-x-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition ${
                    isActive
                      ? 'bg-gray-100 text-gray-900'
                      : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
            {isAuthenticated && (
              <>
                <span className="text-gray-400 mx-2">|</span>
                <span className="text-sm text-gray-600">{user?.username}</span>
                <button
                  onClick={logout}
                  className="ml-2 px-3 py-2 rounded-md text-sm font-medium text-red-600 hover:text-red-800 hover:bg-red-50 transition"
                >
                  Logout
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
