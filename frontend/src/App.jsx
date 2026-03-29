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

    // Step 1: Check localStorage FIRST for instant start
    const saved = localStorage.getItem("vetai_user");
    const savedTgId = localStorage.getItem("vetai_telegram_id");

    if (saved && savedTgId) {
      // User already registered — show app immediately
      setIsOnboarded(true);
      setAuthLoading(false);
    }

    // Step 2: Auth in background (update user data, track login)
    const doAuth = async () => {
      let tgUser;
      try {
        tgUser = WebApp.initDataUnsafe?.user;
      } catch {}
      if (!tgUser || !tgUser.id) {
        tgUser = { id: 12345, first_name: "Dev" };
      }

      localStorage.setItem("vetai_telegram_id", String(tgUser.id));

      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 55000);

        const res = await fetch(`${API_URL}/api/v1/users/auth`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          signal: controller.signal,
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
        clearTimeout(timeout);
        const data = await res.json();

        if (data.is_new) {
          // New user — show onboarding
          setIsOnboarded(false);
          setAuthLoading(false);
        } else {
          // Existing user — update local data from DB
          localStorage.setItem("vetai_user", JSON.stringify(data.user));
          if (!saved) {
            // First time loading (no localStorage yet)
            setIsOnboarded(true);
            setAuthLoading(false);
          }
        }
      } catch (err) {
        console.error("Auth error:", err);
        // If no localStorage and auth failed — still need to handle
        if (!saved) {
          setIsOnboarded(false);
          setAuthLoading(false);
        }
      }
    };

    doAuth();
  }, []);

  if (authLoading || isOnboarded === null) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-3">
        <div className="text-4xl">🐾</div>
        <div className="text-gray-500 text-sm">Подключаемся...</div>
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
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <AppContent />
    </BrowserRouter>
  );
}
