'use client';

import React, { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { decodeSharePayload, type ShareLinkPayload } from '@/shareLinks';

function SharePageInner() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [status, setStatus] = useState<'idle' | 'valid' | 'invalid'>('idle');
  const [summary, setSummary] = useState<string>('');

  useEffect(() => {
    const encoded = searchParams.get('payload');
    if (!encoded) {
      setStatus('invalid');
      return;
    }

    const decoded: ShareLinkPayload | null = decodeSharePayload(encoded);
    if (!decoded) {
      setStatus('invalid');
      return;
    }

    setStatus('valid');

    const stage = decoded.stage || 'unknown';
    const projectName = decoded.data?.projectName || decoded.data?.project_name || '';
    const summaryText = projectName ? `${stage} – ${projectName}` : stage;
    setSummary(summaryText);

    try {
      if (typeof window !== 'undefined') {
        window.sessionStorage.setItem('devussy_share_payload', encoded);
      }
    } catch (err) {
      console.error('[share page] Failed to persist share payload', err);
    }
  }, [searchParams]);

  const handleOpenMainApp = () => {
    router.push('/');
  };

  return (
    <main className="min-h-screen flex items-center justify-center bg-background text-foreground">
      <div className="max-w-lg w-full px-6 py-8 space-y-4 border border-border/40 rounded-xl bg-background/80 shadow-lg">
        <h1 className="text-2xl font-bold tracking-tight">Devussy Share Link</h1>

        {status === 'idle' && (
          <p className="text-sm text-muted-foreground">Validating share link...</p>
        )}

        {status === 'invalid' && (
          <p className="text-sm text-destructive">
            This share link is invalid or has an unsupported payload.
          </p>
        )}

        {status === 'valid' && (
          <>
            <p className="text-sm text-muted-foreground">
              This link contains shared Devussy state
              {summary && (
                <>
                  {' '}
                  for <span className="font-medium text-foreground">{summary}</span>
                </>
              )}
              .
            </p>
            <p className="text-xs text-muted-foreground">
              Click the button below to open the main Devussy desktop. The app will restore this
              shared state and open the appropriate Devussy window.
            </p>
            <Button className="mt-2" onClick={handleOpenMainApp}>
              Open Devussy
            </Button>
          </>
        )}
      </div>
    </main>
  );
}

export default function SharePage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen flex items-center justify-center bg-background text-foreground">
          <div className="max-w-lg w-full px-6 py-8 space-y-4 border border-border/40 rounded-xl bg-background/80 shadow-lg">
            <h1 className="text-2xl font-bold tracking-tight">Devussy Share Link</h1>
            <p className="text-sm text-muted-foreground">Validating share link...</p>
          </div>
        </main>
      }
    >
      <SharePageInner />
    </Suspense>
  );
}
