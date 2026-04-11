import React from 'react';
import { useAppContext } from './stores/appStore';
import { PresentationShell } from './components/PresentationShell';
import { Onboarding } from './components/Onboarding';
import { TrustTransition } from './components/TrustTransition';
import { Login } from './components/Login';
import { FileUploader } from './components/FileUploader';

const AppContent: React.FC = () => {
  const { appView } = useAppContext();

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-8 font-sans">
      <div className="w-full max-w-7xl h-[88vh] main-container flex overflow-hidden">
        {appView === 'booting' && (
          <div className="w-full h-full flex flex-col items-center justify-center">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-400 to-violet-500 animate-pulse mb-4" />
            <p className="text-slate-400 font-medium">Configuring Talk2Data...</p>
          </div>
        )}
        {appView === 'login' && <Login />}
        {appView === 'upload' && <FileUploader />}
        {appView === 'onboarding' && <Onboarding />}
        {appView === 'transition' && <TrustTransition />}
        {appView === 'chat' && <PresentationShell />}
      </div>
    </div>
  );
};

export default AppContent;
