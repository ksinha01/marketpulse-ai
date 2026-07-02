import { AuthProvider, useAuth } from './hooks/useAuth';
import type { UiPathSDKConfig } from '@uipath/uipath-typescript/core';
import Dashboard from './Dashboard';

const authConfig: UiPathSDKConfig = {
  clientId: import.meta.env.VITE_UIPATH_CLIENT_ID,
  orgName: import.meta.env.VITE_UIPATH_ORG_NAME,
  tenantName: import.meta.env.VITE_UIPATH_TENANT_NAME,
  baseUrl: import.meta.env.VITE_UIPATH_BASE_URL,
  redirectUri: window.location.origin + window.location.pathname,
  scope: import.meta.env.VITE_UIPATH_SCOPE,
};

function AppContent() {
  const { isAuthenticated, isLoading, error, login, logout } = useAuth();

  if (isLoading) return <div className="p-8">Loading...</div>;
  if (error) return <div className="p-8 text-red-600">Error: {error}</div>;

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-sm w-full bg-white rounded-lg shadow p-8 text-center">
          <h1 className="text-2xl font-semibold mb-2">MarketPulse</h1>
          <p className="text-gray-600 mb-6">Sign in with your UiPath account to view the dashboard.</p>
          <button
            onClick={login}
            className="w-full py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Sign in with UiPath
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '8px', background: '#0b0e11' }}>
        <button onClick={logout} style={{ fontSize: '12px', color: '#888', background: 'none', border: 'none', cursor: 'pointer' }}>
          Sign out
        </button>
      </div>
      <Dashboard />
    </div>
  );
}

function App() {
  return (
    <AuthProvider config={authConfig}>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
