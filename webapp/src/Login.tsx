import { useState, type FormEvent } from 'react';

// Hardcoded credentials — a basic gate, not real security. Anyone who opens
// browser devtools and reads the bundled JS can see these values; this
// only keeps casual visitors out, it does not protect sensitive data.
const USERNAME = 'admin';
const PASSWORD = 'Dehri@1021';

const SESSION_KEY = 'marketpulse_authed';

export function isAuthed(): boolean {
  return sessionStorage.getItem(SESSION_KEY) === 'true';
}

export default function Login({ onSuccess }: { onSuccess: () => void }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (username === USERNAME && password === PASSWORD) {
      sessionStorage.setItem(SESSION_KEY, 'true');
      setError('');
      onSuccess();
    } else {
      setError('Invalid username or password');
    }
  };

  return (
    <div style={container}>
      <form onSubmit={handleSubmit} style={card}>
        <h1 style={{ marginBottom: '4px' }}>MarketPulse</h1>
        <p style={{ color: '#888', fontSize: '13px', marginBottom: '20px' }}>Sign in to continue</p>

        <label style={label}>Username</label>
        <input
          style={input}
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoFocus
        />

        <label style={label}>Password</label>
        <input
          style={input}
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        {error && <div style={errorStyle}>{error}</div>}

        <button type="submit" style={button}>Sign in</button>
      </form>
    </div>
  );
}

const container: React.CSSProperties = {
  minHeight: '100vh',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  background: '#0b0e11',
  fontFamily: 'system-ui',
};
const card: React.CSSProperties = {
  background: '#111',
  padding: '32px',
  borderRadius: '8px',
  width: '300px',
  color: '#e6edf3',
};
const label: React.CSSProperties = { display: 'block', fontSize: '12px', color: '#888', marginBottom: '4px', marginTop: '12px' };
const input: React.CSSProperties = {
  width: '100%',
  padding: '8px',
  borderRadius: '4px',
  border: '1px solid #333',
  background: '#0b0e11',
  color: '#e6edf3',
  fontSize: '14px',
  boxSizing: 'border-box',
};
const errorStyle: React.CSSProperties = { color: '#ff5252', fontSize: '12px', marginTop: '10px' };
const button: React.CSSProperties = {
  width: '100%',
  marginTop: '20px',
  padding: '10px',
  borderRadius: '4px',
  border: 'none',
  background: '#2563eb',
  color: 'white',
  fontWeight: 600,
  cursor: 'pointer',
};
