import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import WebApp from "@twa-dev/sdk";

import OnboardingPage from "./pages/OnboardingPage";
import HomePage from "./pages/HomePage";
import PhotoUploadPage from "./pages/PhotoUploadPage";
import LabResultsPage from "./pages/LabResultsPage";
import ChatPage from "./pages/ChatPage";
import HistoryPage from "./pages/HistoryPage";
import BottomNav from "./components/BottomNav";

function AppContent() {
  const [isOnboarded, setIsOnboarded] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Init Telegram Mini App
    WebApp.ready();
    WebApp.expand();

    // Check if user already registered
    const saved = localStorage.getItem("vetai_user");
    if (saved) {
      setIsOnboarded(true);
    }
  }, []);

  if (!isOnboarded) {
    return (
      <OnboardingPage
        onComplete={(userData) => {
          localStorage.setItem("vetai_user", JSON.stringify(userData));
          setIsOnboarded(true);
          navigate("/");
        }}
      />
    );
  }

  return (
    <div className="safe-area flex flex-col h-screen">
      <div className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/photo" element={<PhotoUploadPage />} />
          <Route path="/lab" element={<LabResultsPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </div>
      <BottomNav />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}