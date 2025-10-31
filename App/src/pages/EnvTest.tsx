export function EnvTest() {
  const apiUrl = import.meta.env.VITE_API_BASE_URL || 'FALLBACK: http://localhost:8000';
  const fullUrl = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/admin/users`;
  
  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h1>Environment Variable Test</h1>
      <p><strong>VITE_API_BASE_URL:</strong> {apiUrl}</p>
      <p><strong>Full constructed URL:</strong> {fullUrl}</p>
      <p><strong>All env vars:</strong></p>
      <pre>{JSON.stringify(import.meta.env, null, 2)}</pre>
    </div>
  );
}
