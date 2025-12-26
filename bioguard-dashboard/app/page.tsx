'use client';

import { useState } from 'react';
import Link from 'next/link';
import { QRCodeSVG } from 'qrcode.react';
import { v4 as uuidv4 } from 'uuid';

export default function Home() {
  const [merchantName, setMerchantName] = useState('');
  const [webhookUrl, setWebhookUrl] = useState('');
  const [generatedLink, setGeneratedLink] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copiedField, setCopiedField] = useState<'verification' | 'direct' | null>(null);
  const [config, setConfig] = useState({
    check_emulator: true,
    light_sync: true,
    face_liveness: true,
  });

  const generateLink = async () => {
    if (!merchantName.trim()) {
      alert('Please enter merchant name');
      return;
    }

    setIsLoading(true);
    const newSessionId = uuidv4();

    try {
      // In production, this would create a record in Supabase
      // For demo, we just generate the link
      const baseUrl = process.env.NEXT_PUBLIC_APP_URL || window.location.origin;
      const link = `${baseUrl}/verify/${newSessionId}`;

      setSessionId(newSessionId);
      setGeneratedLink(link);
    } catch (error) {
      console.error('Error generating link:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const directLink = sessionId
    ? `bioguard://verify?session_id=${sessionId}`
    : '';

  const copyToClipboard = async (
    value: string,
    field: 'verification' | 'direct',
  ) => {
    if (!value) return;
    await navigator.clipboard.writeText(value);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  return (
    <div className="min-h-screen px-6 py-10 lg:px-12">
      {/* Header */}
      <header className="max-w-6xl mx-auto mb-12">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-primary-900 flex items-center justify-center shadow-lg">
              <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <h1 className="text-2xl font-semibold heading text-ink">
                BioGuard Nexus
              </h1>
              <p className="text-sm text-slate-500">Merchant Dashboard</p>
            </div>
          </div>
          <Link
            href="/dashboard"
            className="px-4 py-2 rounded-lg bg-primary-700 text-white hover:bg-primary-800 transition-colors"
          >
            View Sessions
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto">
        <div className="grid md:grid-cols-2 gap-8">
          {/* Link Generator */}
          <div className="glass rounded-2xl p-6">
            <h2 className="text-xl font-semibold heading text-ink mb-6">
              Generate Verification Link
            </h2>

            <div className="space-y-4">
              {/* Merchant Name */}
              <div>
                <label className="block text-sm text-slate-600 mb-2">Merchant Name</label>
                <input
                  type="text"
                  value={merchantName}
                  onChange={(e) => setMerchantName(e.target.value)}
                  placeholder="Enter your business name"
                  className="w-full px-4 py-3 bg-white border border-slate-200 rounded-lg focus:outline-none focus:border-primary-500 transition-colors text-slate-900"
                />
              </div>

              {/* Webhook URL (Optional) */}
              <div>
                <label className="block text-sm text-slate-600 mb-2">Webhook URL (Optional)</label>
                <input
                  type="url"
                  value={webhookUrl}
                  onChange={(e) => setWebhookUrl(e.target.value)}
                  placeholder="https://your-api.com/webhook"
                  className="w-full px-4 py-3 bg-white border border-slate-200 rounded-lg focus:outline-none focus:border-primary-500 transition-colors text-slate-900"
                />
              </div>

              {/* Verification Options */}
              <div>
                <label className="block text-sm text-slate-600 mb-3">Verification Modules</label>
                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={config.check_emulator}
                      onChange={(e) => setConfig({ ...config, check_emulator: e.target.checked })}
                      className="w-5 h-5 rounded border-slate-300 text-primary-600 focus:ring-primary-500 bg-white"
                    />
                    <span className="flex items-center gap-2 text-slate-700">
                      <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
                      Environment Shield (Root/Emulator Detection)
                    </span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={config.light_sync}
                      onChange={(e) => setConfig({ ...config, light_sync: e.target.checked })}
                      className="w-5 h-5 rounded border-slate-300 text-primary-600 focus:ring-primary-500 bg-white"
                    />
                    <span className="flex items-center gap-2 text-slate-700">
                      <span className="w-2 h-2 bg-accent-400 rounded-full"></span>
                      Light-Sync Challenge (Physics Verification)
                    </span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={config.face_liveness}
                      onChange={(e) => setConfig({ ...config, face_liveness: e.target.checked })}
                      className="w-5 h-5 rounded border-slate-300 text-primary-600 focus:ring-primary-500 bg-white"
                    />
                    <span className="flex items-center gap-2 text-slate-700">
                      <span className="w-2 h-2 bg-primary-700 rounded-full"></span>
                      AI Face Liveness (MiniFASNet)
                    </span>
                  </label>
                </div>
              </div>

              {/* Generate Button */}
              <button
                onClick={generateLink}
                disabled={isLoading}
                className="w-full py-3 bg-primary-700 hover:bg-primary-800 text-white rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Generating...' : 'Generate Link'}
              </button>
            </div>
          </div>

          {/* QR Code & Link Display */}
          <div className="glass rounded-2xl p-6">
            <h2 className="text-xl font-semibold heading text-ink mb-6">
              Verification Package
            </h2>

            {generatedLink ? (
              <div className="space-y-6">
                {/* QR Code */}
                <div className="flex justify-center">
                  <div className="p-4 bg-white rounded-xl border border-slate-200">
                    <QRCodeSVG value={generatedLink} size={200} />
                  </div>
                </div>

                {/* Session ID */}
                <div className="text-center">
                  <p className="text-sm text-slate-500 mb-1">Session ID</p>
                  <p className="font-mono text-sm text-primary-700">{sessionId}</p>
                </div>

                {/* Link */}
                <div>
                  <p className="text-sm text-slate-600 mb-2">Verification URL</p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={generatedLink}
                      readOnly
                      className="flex-1 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-mono text-slate-700"
                    />
                    <button
                      onClick={() => copyToClipboard(generatedLink, 'verification')}
                      className="px-4 py-2 bg-primary-700 text-white hover:bg-primary-800 rounded-lg transition-colors"
                    >
                      {copiedField === 'verification' ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                  <p className="mt-2 text-xs text-slate-500">
                    Share this URL or QR code. When opened on Android, it will
                    launch the app automatically.
                  </p>
                </div>

                {/* Deep Link */}
                <div>
                  <p className="text-sm text-slate-600 mb-2">Direct App Link</p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={directLink}
                      readOnly
                      className="flex-1 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-mono text-slate-700"
                    />
                    <button
                      onClick={() => copyToClipboard(directLink, 'direct')}
                      className="px-4 py-2 bg-slate-900 text-white hover:bg-slate-800 rounded-lg transition-colors"
                    >
                      {copiedField === 'direct' ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                  <p className="mt-2 text-xs text-slate-500">
                    Use this when the app is already installed. You can paste
                    it into the BioGuard app’s session field or open it in a
                    mobile browser.
                  </p>
                </div>

                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm font-semibold text-slate-800 mb-2">
                    How to use these links
                  </p>
                  <ol className="space-y-2 text-xs text-slate-600">
                    <li>
                      1. Send the Verification URL (or QR code) to your user.
                    </li>
                    <li>
                      2. The user opens it on Android — the app launches with
                      the session ready.
                    </li>
                    <li>
                      3. If the app isn’t installed, they’ll see the download
                      prompt.
                    </li>
                    <li>
                      4. For in-app flows, use the Direct App Link and paste it
                      in the app.
                    </li>
                  </ol>
                </div>
                <div className="rounded-xl border border-accent-200 bg-accent-50 p-4">
                  <p className="text-sm font-semibold text-ink mb-1">
                    Troubleshooting
                  </p>
                  <p className="text-xs text-slate-600">
                    If verification fails instantly, ensure Developer Options
                    and USB Debugging are disabled on the device before retrying.
                  </p>
                </div>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-slate-500">
                <div className="text-center">
                  <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
                  </svg>
                  <p>Generate a link to see QR code</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-12 grid md:grid-cols-3 gap-6">
          <div className="glass rounded-xl p-6">
            <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-ink mb-2 heading">
              Environment Shield
            </h3>
            <p className="text-sm text-slate-600">
              Detects root access, emulators, USB debugging, and hooking
              frameworks like Frida.
            </p>
          </div>

          <div className="glass rounded-xl p-6">
            <div className="w-12 h-12 bg-accent-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-accent-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-ink mb-2 heading">
              Light-Sync Challenge
            </h3>
            <p className="text-sm text-slate-600">
              Physics-based verification using screen flash and camera to
              detect spoofing attempts.
            </p>
          </div>

          <div className="glass rounded-xl p-6">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-primary-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-ink mb-2 heading">
              AI Face Liveness
            </h3>
            <p className="text-sm text-slate-600">
              MiniFASNetV2 deep learning model detects photos, videos, and 3D
              masks.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
