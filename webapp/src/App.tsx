import { useState } from 'react';
import Login, { isAuthed } from './Login';
import Dashboard from './Dashboard';

function App() {
  const [authed, setAuthed] = useState(isAuthed());

  if (!authed) {
    return <Login onSuccess={() => setAuthed(true)} />;
  }

  const signOut = () => {
    sessionStorage.removeItem('marketpulse_authed');
    setAuthed(false);
  };

  return (
    <div className="min-h-screen">
      <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '8px', background: '#0b0e11' }}>
        <button onClick={signOut} style={{ fontSize: '12px', color: '#888', background: 'none', border: 'none', cursor: 'pointer' }}>
          Sign out
        </button>
      </div>
      <Dashboard />
    </div>
  );
}

export default App;
