import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Camera, FileText, MessageCircle, Gift, Flame, ShieldCheck } from "lucide-react";
import { t } from "../i18n";
import { track, shareInvite } from "../analytics";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function HomePage() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("vetai_user") || "{}");
  const [usageToday, setUsageToday] = useState(0);
  const [usageLimit, setUsageLimit] = useState(3);
  const [streak, setStreak] = useState(0);
  const [referralCount, setReferralCount] = useState(0);
  const [totalChecks, setTotalChecks] = useState(0);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackText, setFeedbackText] = useState("");
  const [feedbackSent, setFeedbackSent] = useState(false);

  const actions = [
    {
      icon: Camera,
      title: t("photoCheckTitle"),
      desc: t("photoCheckDesc"),
      path: "/photo",
      color: "#2AABEE",
    },
    {
      icon: FileText,
      title: t("labUploadTitle"),
      desc: t("labUploadDesc"),
      path: "/lab",
      color: "#FF9800",
    },
    {
      icon: MessageCircle,
      title: t("symptomChatTitle"),
      desc: t("symptomChatDesc"),
      path: "/chat",
      color: "#4CAF50",
    },
  ];

  useEffect(() => {
    const telegramId = localStorage.getItem("vetai_telegram_id") || "12345";
    const fetchUsage = async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/users/me`, {
          headers: { "x-telegram-id": telegramId },
        });
        if (res.ok) {
          const data = await res.json();
          setUsageToday(data.usage_today || 0);
          if (data.usage_limit) setUsageLimit(data.usage_limit);
          setStreak(data.streak || 0);
          setReferralCount(data.referral_count || 0);
        }
      } catch (err) {
        console.error("Failed to fetch usage:", err);
      }
    };
    const fetchTrust = async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/analytics/public-stats`);
        if (res.ok) {
          const data = await res.json();
          setTotalChecks(data.checks || 0);
        }
      } catch {}
    };
    fetchUsage();
    fetchTrust();
  }, []);

  const remaining = Math.max(0, usageLimit - usageToday);

  return (
    <div className="px-4 py-3">
      {/* Greeting + streak */}
      <div className="mb-3 flex items-start justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {t("greeting")}{user.petName || (user.pets && user.pets[0]?.name) ? `, ${user.petName || user.pets[0]?.name}` : ""}! 🐾
          </h1>
          <p className="text-gray-500 mt-1">{t("healthQuestion")}</p>
        </div>
        {streak > 0 && (
          <div className="shrink-0 flex items-center gap-1 px-2.5 py-1.5 rounded-full bg-orange-50 border border-orange-200 text-orange-600 text-sm font-semibold">
            <Flame size={16} /> {streak} <span className="text-xs font-normal">{t("streakDaysLabel")}</span>
          </div>
        )}
      </div>

      {/* Beta banner with remaining requests */}
      <div className="mb-3 px-3 py-1.5 rounded-xl bg-green-50 border border-green-200 text-center text-sm text-green-700">
        {t("betaBanner")} {usageToday}/{usageLimit}
      </div>

      {/* Trust signal — social proof */}
      {totalChecks > 0 && (
        <div className="mb-3 flex items-center justify-center gap-1.5 text-xs text-gray-500">
          <ShieldCheck size={14} className="text-green-500" />
          {totalChecks.toLocaleString("ru-RU")} {t("trustCheckedSuffix")}
        </div>
      )}

      {/* Action cards */}
      <div className="space-y-2">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.path}
              onClick={() => navigate(action.path)}
              className="w-full flex items-center gap-4 p-4 rounded-2xl bg-white border border-gray-100 shadow-sm hover:shadow-md transition-shadow text-left"
            >
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{ background: `${action.color}15` }}
              >
                <Icon size={24} color={action.color} />
              </div>
              <div>
                <div className="font-semibold text-gray-900">{action.title}</div>
                <div className="text-sm text-gray-500">{action.desc}</div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Health tip */}
      <div className="mt-3 p-3 rounded-2xl bg-blue-50 border border-blue-100">
        <div className="text-sm font-semibold text-tg-blue mb-1">{t("dailyTipTitle")}</div>
        <div className="text-sm text-gray-600">
          {t("dailyTipText")}
        </div>
      </div>

      {/* Invite friends — viral loop */}
      <div className="mt-3 p-4 rounded-2xl bg-gradient-to-br from-violet-50 to-blue-50 border border-violet-100">
        <div className="flex items-center gap-2 mb-1">
          <Gift size={18} className="text-violet-600" />
          <span className="font-semibold text-gray-900">{t("inviteTitle")}</span>
        </div>
        <p className="text-sm text-gray-600 mb-3">{t("inviteDesc")}</p>
        <button
          onClick={() => shareInvite()}
          className="w-full bg-violet-600 text-white text-sm font-semibold py-2.5 rounded-xl active:opacity-80"
        >
          {t("inviteButton")}
        </button>
        {referralCount > 0 && (
          <div className="mt-2 text-center text-xs text-violet-700">
            {t("inviteCountLabel")} {referralCount}
          </div>
        )}
      </div>

      {/* Feedback */}
      <div className="mt-2">
        {!showFeedback ? (
          <button
            onClick={() => setShowFeedback(true)}
            className="w-full text-center text-xs text-gray-400 py-2"
          >
            {t("feedbackButton")}
          </button>
        ) : (
          <div className="p-4 rounded-2xl bg-gray-50 border border-gray-200">
            <div className="text-sm font-semibold text-gray-700 mb-2">{t("feedbackTitle")}</div>
            <textarea
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
              placeholder={t("feedbackPlaceholder")}
              className="w-full px-3 py-2 rounded-xl border border-gray-200 focus:border-tg-blue focus:outline-none text-sm text-gray-900 resize-none"
              rows={3}
            />
            <div className="flex gap-2 mt-2">
              <button
                onClick={async () => {
                  if (!feedbackText.trim()) return;
                  const telegramId = localStorage.getItem("vetai_telegram_id") || "12345";
                  try {
                    await fetch(`${API_URL}/api/v1/users/feedback`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json", "x-telegram-id": telegramId },
                      body: JSON.stringify({ message: feedbackText.trim() }),
                    });
                    setFeedbackText("");
                    setShowFeedback(false);
                    setFeedbackSent(true);
                    setTimeout(() => setFeedbackSent(false), 3000);
                  } catch {}
                }}
                className="flex-1 bg-tg-blue text-white text-sm font-medium py-2 rounded-xl"
              >
                {t("feedbackSend")}
              </button>
              <button
                onClick={() => { setShowFeedback(false); setFeedbackText(""); }}
                className="px-4 text-sm text-gray-400"
              >
                {t("feedbackCancel")}
              </button>
            </div>
          </div>
        )}
        {feedbackSent && (
          <div className="mt-2 text-center text-xs text-green-600">{t("feedbackThanks")}</div>
        )}
      </div>
      <div className="text-center text-[9px] text-gray-300 mt-2">v1.4.0</div>
    </div>
  );
}
