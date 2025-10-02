export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen grid grid-cols-[240px_1fr]">
      <aside className="border-r p-4">
        <div className="text-lg font-semibold mb-4">Vendor Console</div>
        <nav className="space-y-2 text-sm">
          <a className="block hover:underline" href="/dashboard">Home</a>
          <a className="block hover:underline" href="/dashboard/search">Search</a>
          <a className="block hover:underline" href="/dashboard/settings">Settings</a>
        </nav>
      </aside>
      <main className="p-6">
        {children}
      </main>
    </div>
  );
}
