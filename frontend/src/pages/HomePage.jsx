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

  const remaining = Math.max(0, usageLimit - usageToday);

  return (
    <div className="px-4 py-6">
      {/* Greeting */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Привет{user.petName || (user.pets && user.pets[0]?.name) ? `, ${user.petName || user.pets[0]?.name}` : ""}! 🐾
        </h1>
        <p className="text-gray-500 mt-1">Как здоровье вашего питомца?</p>
      </div>

      {/* Beta banner with remaining requests */}
      <div className="mb-4 px-3 py-2 rounded-xl bg-green-50 border border-green-200 text-center text-sm text-green-700">
        Бета — бесплатно! Использовано: {usageToday}/{usageLimit}
      </div>

      {/* Action cards */}
      <div className="space-y-3">
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
      <div className="mt-6 p-4 rounded-2xl bg-blue-50 border border-blue-100">
        <div className="text-sm font-semibold text-tg-blue mb-1">💡 Совет дня</div>
        <div className="text-sm text-gray-600">
          Регулярно проверяйте уши питомца — покраснение или запах могут указывать
          на отит. Загрузите фото для быстрой проверки!
        </div>
      </div>

      {/* Feedback */}
      <div className="mt-8 text-center text-xs text-gray-400">
        Обратная связь:{" "}
        <a
          href="https://t.me/Andrew_Konstaninov"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-gray-500"
        >
          @Andrew_Konstaninov
        </a>
      </div>
    </div>
  );
}
