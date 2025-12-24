'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

export default function VerifyPage() {
  const params = useParams();
  const sessionId = params.id as string;
  const [status, setStatus] = useState('Checking device...');
  const [isAndroid, setIsAndroid] = useState(false);
  const [countdown, setCountdown] = useState(3);

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

  return (
    <div className="min-h-screen flex items-center justify-center p-8">
      <div className="glass rounded-3xl p-8 max-w-md w-full text-center">
        {/* Logo */}
        <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center">
          <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>

        <h1 className="text-2xl font-bold gradient-text mb-2">BioGuard Nexus</h1>
        <p className="text-gray-400 mb-8">Security Verification</p>

        {/* Session Info */}
        <div className="mb-8 p-4 bg-slate-800/50 rounded-xl">
          <p className="text-xs text-gray-500 mb-1">Session ID</p>
          <p className="font-mono text-sm text-primary-400 break-all">{sessionId}</p>
        </div>

        {/* Status */}
        <div className="mb-8">
          {isAndroid && countdown > 0 ? (
            <div className="flex items-center justify-center gap-3">
              <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-gray-300">{status}</span>
            </div>
          ) : (
            <p className="text-gray-300">{status}</p>
          )}
        </div>

        {/* Manual Open Button */}
        {isAndroid && (
          <button
            onClick={handleManualOpen}
            className="w-full py-4 bg-gradient-to-r from-primary-500 to-purple-600 hover:from-primary-600 hover:to-purple-700 rounded-xl font-medium transition-all mb-4"
          >
            Open BioGuard App
          </button>
        )}

        {/* Download Link */}
        <a
          href="https://play.google.com/store/apps/details?id=com.bioguard.nexus"
          className="block w-full py-4 bg-slate-700 hover:bg-slate-600 rounded-xl font-medium transition-colors"
        >
          Download App
        </a>

        {/* Security Notice */}
        <div className="mt-8 p-4 bg-green-500/10 border border-green-500/20 rounded-xl">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-green-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <div className="text-left">
              <p className="text-sm text-green-400 font-medium">Secure Verification</p>
              <p className="text-xs text-gray-400 mt-1">
                This verification process runs entirely on your device. No facial data is stored on our servers.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
