'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

export default function VerifyPage() {
  const params = useParams();
  const sessionId = params.id as string;
  const [status, setStatus] = useState('Checking device...');
  const [isAndroid, setIsAndroid] = useState(false);
  const [countdown, setCountdown] = useState(3);
  const [copied, setCopied] = useState(false);
  const directLink = `bioguard://verify?session_id=${sessionId}`;

  useEffect(() => {
    const userAgent = navigator.userAgent || (navigator as any).vendor || '';
    const isAndroidDevice = /android/i.test(userAgent);
    setIsAndroid(isAndroidDevice);

    if (isAndroidDevice) {
      setStatus('Launching BioGuard App...');

      // Deep link URL
      const appUrl = `bioguard://verify?session_id=${sessionId}`;
      const storeUrl = 'https://play.google.com/store/apps/details?id=com.bioguard.nexus';

      // Try to open the app
      const start = Date.now();
      window.location.href = appUrl;

      // Countdown for redirect to store
      const countdownInterval = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(countdownInterval);
            // If still on this page after timeout, redirect to store
            if (Date.now() - start < 3000) {
              setStatus('App not found. Redirecting to download...');
              setTimeout(() => {
                window.location.href = storeUrl;
              }, 1000);
            }
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(countdownInterval);
    } else {
      setStatus('Please open this link on an Android device');
    }
  }, [sessionId]);

  const handleManualOpen = () => {
    window.location.href = `bioguard://verify?session_id=${sessionId}`;
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(directLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-10">
      <div className="glass rounded-3xl p-8 max-w-md w-full text-center">
        {/* Logo */}
        <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-primary-900 flex items-center justify-center shadow-lg">
          <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>

        <h1 className="text-2xl font-semibold heading text-ink mb-2">
          BioGuard Nexus
        </h1>
        <p className="text-slate-500 mb-8">Security Verification</p>

        {/* Session Info */}
        <div className="mb-8 p-4 bg-slate-50 rounded-xl border border-slate-200">
          <p className="text-xs text-slate-500 mb-1">Session ID</p>
          <p className="font-mono text-sm text-primary-700 break-all">{sessionId}</p>
        </div>

        {/* Status */}
        <div className="mb-8">
          {isAndroid && countdown > 0 ? (
            <div className="flex items-center justify-center gap-3">
              <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-slate-600">{status}</span>
            </div>
          ) : (
            <p className="text-slate-600">{status}</p>
          )}
        </div>

        {/* Manual Open Button */}
        {isAndroid && (
          <button
            onClick={handleManualOpen}
            className="w-full py-4 bg-primary-700 text-white hover:bg-primary-800 rounded-xl font-medium transition-all mb-4"
          >
            Open BioGuard App
          </button>
        )}

        {/* Download Link */}
        <a
          href="https://play.google.com/store/apps/details?id=com.bioguard.nexus"
          className="block w-full py-4 bg-slate-900 text-white hover:bg-slate-800 rounded-xl font-medium transition-colors"
        >
          Download App
        </a>

        {/* Direct Link Copy */}
        <div className="mt-6 text-left">
          <p className="text-xs font-semibold text-slate-700 mb-2">
            Direct App Link
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              readOnly
              value={directLink}
              className="flex-1 px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs font-mono text-slate-700"
            />
            <button
              onClick={handleCopy}
              className="px-3 py-2 bg-primary-700 text-white rounded-lg text-xs hover:bg-primary-800"
            >
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
          <p className="mt-2 text-xs text-slate-500">
            Paste this into the BioGuard app if the auto-launch doesn’t work.
          </p>
        </div>

        {/* Security Notice */}
        <div className="mt-8 p-4 bg-primary-50 border border-primary-100 rounded-xl">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-primary-700 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <div className="text-left">
              <p className="text-sm text-primary-700 font-medium">Secure Verification</p>
              <p className="text-xs text-slate-500 mt-1">
                This verification process runs entirely on your device. No facial data is stored on our servers.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
