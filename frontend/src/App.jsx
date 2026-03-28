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

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function detectPlatform() {
  try {
    if (WebApp.platform) return WebApp.platform;
  } catch {}
  const ua = navigator.userAgent.toLowerCase();
  if (/iphone|ipad|ipod/.test(ua)) return "ios";
  if (/android/.test(ua)) return "android";
  if (/macintosh|windows|linux/.test(ua)) return "desktop";
  return "web";
}

function AppContent() {
  const [isOnboarded, setIsOnboarded] = useState(null); // null = loading
  const [authLoading, setAuthLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // Init Telegram Mini App
    WebApp.ready();
    WebApp.expand();

    const doAuth = async () => {
      // Get telegram user data (with dev fallback)
      let tgUser;
      try {
        tgUser = WebApp.initDataUnsafe?.user;
      } catch {}
      if (!tgUser || !tgUser.id) {
        tgUser = { id: 12345, first_name: "Dev" };
      }

      // Store telegram_id for all pages
      localStorage.setItem("vetai_telegram_id", String(tgUser.id));

      try {
        const res = await fetch(`${API_URL}/api/v1/users/auth`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            telegram_id: tgUser.id,
            first_name: tgUser.first_name,
            last_name: tgUser.last_name || null,
            username: tgUser.username || null,
            language_code: tgUser.language_code || "ru",
            is_premium: tgUser.is_premium || false,
            platform: detectPlatform(),
          }),
        });
        const data = await res.json();

        if (data.is_new) {
          setIsOnboarded(false);
        } else {
          // Save user data from DB
          localStorage.setItem("vetai_user", JSON.stringify(data.user));
          setIsOnboarded(true);
        }
      } catch (err) {
        console.error("Auth error:", err);
        // Fallback: check localStorage
        const saved = localStorage.getItem("vetai_user");
        setIsOnboarded(!!saved);
      } finally {
        setAuthLoading(false);
      }
    };

    doAuth();
  }, []);

  if (authLoading || isOnboarded === null) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-gray-400 text-lg">Загрузка...</div>
      </div>
    );
  }

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
