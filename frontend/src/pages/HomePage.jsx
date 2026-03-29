import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Camera, FileText, MessageCircle } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const actions = [
  {
    icon: Camera,
    title: "Проверка по фото",
    desc: "Сфотографируйте проблемную область",
    path: "/photo",
    color: "#2AABEE",
  },
  {
    icon: FileText,
    title: "Загрузить анализы",
    desc: "AI расшифрует результаты",
    path: "/lab",
    color: "#FF9800",
  },
  {
    icon: MessageCircle,
    title: "Описать симптомы",
    desc: "Чат с AI-ветеринаром",
    path: "/chat",
    color: "#4CAF50",
  },
];

export default function HomePage() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("vetai_user") || "{}");
  const [usageToday, setUsageToday] = useState(0);
  const [usageLimit, setUsageLimit] = useState(3);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackText, setFeedbackText] = useState("");
  const [feedbackSent, setFeedbackSent] = useState(false);

  useEffect(() => {
    const fetchUsage = async () => {
      const telegramId = localStorage.getItem("vetai_telegram_id") || "12345";
      try {
        const res = await fetch(`${API_URL}/api/v1/users/me`, {
          headers: { "x-telegram-id": telegramId },
        });
        if (res.ok) {
          const data = await res.json();
          setUsageToday(data.usage_today || 0);
          if (data.usage_limit) setUsageLimit(data.usage_limit);
        }
      } catch (err) {
        console.error("Failed to fetch usage:", err);
      }
    };
    fetchUsage();
  }, []);

  return (
    <div className="px-4 py-3 flex flex-col h-full justify-between">
      {/* Top: greeting */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">
          Привет{user.petName || (user.pets && user.pets[0]?.name) ? `, ${user.petName || user.pets[0]?.name}` : ""}! 🐾
        </h1>
        <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded-lg">
          {usageToday}/{usageLimit}
        </span>
      </div>

      {/* Middle: action cards fill space */}
      {actions.map((action) => {
        const Icon = action.icon;
        return (
          <button
            key={action.path}
            onClick={() => navigate(action.path)}
            className="w-full flex items-center gap-4 px-4 py-5 rounded-2xl bg-white border border-gray-100 shadow-sm text-left"
          >
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: `${action.color}15` }}
            >
              <Icon size={24} color={action.color} />
            </div>
            <div>
              <div className="font-semibold text-gray-900">{action.title}</div>
              <div className="text-xs text-gray-500">{action.desc}</div>
            </div>
          </button>
        );
      })}

      {/* Bottom: tip + feedback */}
      <div>
        <div className="p-2.5 rounded-xl bg-blue-50 border border-blue-100 mb-2">
          <div className="text-xs text-gray-600">
            <span className="font-semibold text-tg-blue">💡 </span>
            Регулярно проверяйте уши питомца — покраснение или запах могут указывать на отит.
          </div>
        </div>

        {!showFeedback ? (
          <button
            onClick={() => setShowFeedback(true)}
            className="w-full py-2 rounded-xl bg-white border border-gray-200 text-xs text-gray-500 font-medium"
          >
            💬 Оставить отзыв или предложение
          </button>
        ) : (
          <div className="p-3 rounded-xl bg-gray-50 border border-gray-200">
            <textarea
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
              placeholder="Ваш отзыв или предложение..."
              className="w-full px-3 py-2 rounded-lg border border-gray-200 focus:border-tg-blue focus:outline-none text-sm text-gray-900 resize-none"
              rows={2}
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
                className="flex-1 bg-tg-blue text-white text-sm font-medium py-2 rounded-lg"
              >
                Отправить
              </button>
              <button
                onClick={() => { setShowFeedback(false); setFeedbackText(""); }}
                className="px-3 text-sm text-gray-400"
              >
                Отмена
              </button>
            </div>
          </div>
        )}
        {feedbackSent && (
          <div className="mt-1 text-center text-xs text-green-600">Спасибо за отзыв!</div>
        )}
      </div>
    </div>
  );
}
