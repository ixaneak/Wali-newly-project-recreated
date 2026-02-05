'use client'

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string }
    reset: () => void
}) {
    return (
        <div style={{ padding: '2rem', fontFamily: 'monospace' }}>
            <h2 style={{ color: 'red' }}>Something went wrong!</h2>
            <pre style={{ background: '#f0f0f0', padding: '1rem', overflow: 'auto' }}>
                {error.message}
            </pre>
            <pre style={{ background: '#f0f0f0', padding: '1rem', overflow: 'auto', fontSize: '12px' }}>
                {error.stack}
            </pre>
            <button onClick={() => reset()} style={{ marginTop: '1rem', padding: '0.5rem 1rem' }}>
                Try again
            </button>
        </div>
    )
}
