import { useState, useEffect } from "react";
import { Camera, FileText, MessageCircle, Clock } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const typeIcons = {
  photo: Camera,
  lab_results: FileText,
  chat: MessageCircle,
};

const typeLabels = {
  photo: "Фото",
  lab_results: "Анализы",
  chat: "Чат",
};

export default function HistoryPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const telegramId = localStorage.getItem("vetai_telegram_id") || "12345";
    fetch(`${API_URL}/api/v1/diagnosis/history`, {
      headers: { "x-telegram-id": telegramId },
    })
      .then((r) => r.json())
      .then((data) => setItems(data.items || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        Загрузка...
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 px-6">
        <Clock size={48} className="mb-4" />
        <div className="text-lg font-medium">Пока пусто</div>
        <div className="text-sm text-center mt-2">
          Здесь будут сохраняться результаты проверок вашего питомца
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-6">
      <h1 className="text-xl font-bold mb-4 text-gray-900">История проверок</h1>
      <div className="space-y-3">
        {items.map((item, i) => {
          const Icon = typeIcons[item.type] || Clock;
          return (
            <div
              key={i}
              className="p-4 rounded-2xl bg-white border border-gray-100 shadow-sm flex items-center gap-3"
            >
              <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
                <Icon size={20} className="text-tg-blue" />
              </div>
              <div className="flex-1">
                <div className="font-semibold text-sm text-gray-900">{item.condition || typeLabels[item.type]}</div>
                <div className="text-xs text-gray-400">{item.created_at}</div>
              </div>
              {item.severity && (
                <span
                  className={`text-xs font-medium px-2 py-1 rounded-full ${
                    item.severity === "high"
                      ? "bg-red-100 text-red-600"
                      : item.severity === "medium"
                      ? "bg-yellow-100 text-yellow-700"
                      : "bg-green-100 text-green-600"
                  }`}
                >
                  {item.severity}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}