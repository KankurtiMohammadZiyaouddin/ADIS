import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function LoginPage() {
  const [investigatorId, setInvestigatorId] = useState('');
  const [passphrase, setPassphrase] = useState('');
  const navigate = useNavigate();

  function handleSubmit(e) {
    e.preventDefault();
    navigate('/');
  }

  return (
    <div className="min-h-screen flex items-center justify-center font-body-md text-on-surface bg-background">
  <div>
    <div className="w-full max-w-[420px] px-gutter">
      {/* Logo Container */}
      <div className="flex justify-center mb-8">
        <img alt="ADIS System Logo" className="h-24 w-24 object-contain rounded-lg" src="https://lh3.googleusercontent.com/aida/AEtjO1X8tSpKLcnGoeY9h1x36iQa_M5gVDRMjeuFWGyLcRj6eP88v7B8mdM4jvyPnh5GiqitI5yxdjzHuDeKCNJsC12fHklqMkJq9oXbEZqUlw_HMIVymSwbMY1k-L5dJqACXcVSF3X_a-GuPLMeitQOMxKX8Mqkd6w1hvL9jRaoVjsdSvR6-t02MfjuxxAjtUtfwtdp2nr0S0IdsKmrEicyCe8eitkYKyzq5fJmTuRcYDw6G5vHLqxLXkoajg" />
      </div>
      {/* Login Card */}
      <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-padding-spacious system-shadow">
        <div className="text-center mb-8">
          <h1 className="font-headline-md text-headline-md text-on-surface mb-2">ADIS Authentication</h1>
          <p className="font-body-sm text-body-sm text-on-surface-variant">Authorized investigative personnel only.</p>
        </div>
        <form className="space-y-6" onSubmit={handleSubmit}>
          {/* Investigator ID Field */}
          <div>
            <label className="block text-label-md text-on-surface-variant mb-2" htmlFor="investigator-id">Investigator ID</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <span className="material-symbols-outlined text-outline">badge</span>
              </span>
              <input className="input-transition block w-full pl-10 pr-3 py-2 border border-outline-variant rounded bg-surface-container-lowest font-body-md text-body-md text-on-surface focus:outline-none focus:ring-0" id="investigator-id" name="investigator-id" placeholder="e.g. INV-8472" required type="text" value={investigatorId} onChange={(e) => setInvestigatorId(e.target.value)} />
            </div>
          </div>
          {/* Passphrase Field */}
          <div>
            <label className="block text-label-md text-on-surface-variant mb-2" htmlFor="passphrase">Secure Passphrase</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <span className="material-symbols-outlined text-outline">key</span>
              </span>
              <input className="input-transition block w-full pl-10 pr-3 py-2 border border-outline-variant rounded bg-surface-container-lowest font-body-md text-body-md text-on-surface focus:outline-none focus:ring-0" id="passphrase" name="passphrase" placeholder="••••••••••••" required type="password" value={passphrase} onChange={(e) => setPassphrase(e.target.value)} />
            </div>
          </div>
          {/* Action Button */}
          <button className="w-full flex justify-center py-2 px-4 border border-transparent rounded-DEFAULT shadow-sm text-label-md text-on-primary bg-primary hover:bg-on-primary-fixed-variant focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary transition-colors" type="submit">
            Authenticate Session
          </button>
        </form>
        {/* Contextual Link */}
        <div className="mt-6 text-center">
          <a className="text-label-sm text-primary hover:text-on-primary-fixed-variant transition-colors" href="#">Request Access credentials</a>
        </div>
      </div>
      {/* Security Footer */}
      <div className="mt-8 text-center flex flex-col items-center justify-center gap-2">
        <span className="material-symbols-outlined text-outline-variant text-[16px]">enhanced_encryption</span>
        <p className="text-label-sm text-outline-variant uppercase tracking-wider">Secure Encrypted Forensic Environment</p>
        <p className="text-label-sm text-outline-variant opacity-70">Node: US-EAST-B1 · Env: PRD · v2.4.1</p>
      </div>
    </div>
  </div>
    </div>
  );
}

