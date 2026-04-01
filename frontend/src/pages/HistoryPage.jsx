import { useState, useEffect } from "react";
import { Camera, FileText, MessageCircle, Clock } from "lucide-react";
import { t } from "../i18n";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const typeIcons = {
  photo: Camera,
  lab_results: FileText,
  chat: MessageCircle,
};

export default function HistoryPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);

  const typeLabels = {
    photo: t("historyPhoto"),
    lab_results: t("historyLab"),
    chat: t("historyChat"),
  };

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
        {t("historyLoading")}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 px-6">
        <Clock size={48} className="mb-4" />
        <div className="text-lg font-medium">{t("historyEmpty")}</div>
        <div className="text-sm text-center mt-2">
          {t("historyEmptyDesc")}
        </div>
      </div>
    );
  }

  const getSeverityLabel = (severity) => {
    if (severity === "экстренная" || severity === "emergency") return t("historyEmergency");
    if (severity === "высокая" || severity === "high") return t("historyUrgent");
    if (severity === "средняя" || severity === "medium") return t("historyAttention");
    return t("historyNormal");
  };

  const getSeverityClass = (severity) => {
    if (severity === "экстренная" || severity === "высокая" || severity === "emergency" || severity === "high")
      return "bg-red-100 text-red-600";
    if (severity === "средняя" || severity === "medium")
      return "bg-yellow-100 text-yellow-700";
    return "bg-green-100 text-green-600";
  };

  return (
    <div className="px-4 py-6">
      <h1 className="text-xl font-bold mb-4 text-gray-900">{t("historyTitle")}</h1>
      <div className="space-y-3">
        {items.map((item, i) => {
          const Icon = typeIcons[item.type] || Clock;
          const isOpen = selectedId === i;
          const result = item.result_json;
          return (
            <div
              key={i}
              className="rounded-2xl bg-white border border-gray-100 shadow-sm overflow-hidden"
            >
              <button
                onClick={() => setSelectedId(isOpen ? null : i)}
                className="w-full p-4 flex items-center gap-3 text-left"
              >
                <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center shrink-0">
                  <Icon size={20} className="text-tg-blue" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-sm text-gray-900">{item.condition || typeLabels[item.type]}</div>
                  <div className="text-xs text-gray-400">{item.created_at}</div>
                </div>
                {item.severity && (
                  <span
                    className={`text-xs font-medium px-2 py-1 rounded-full shrink-0 ${getSeverityClass(item.severity)}`}
                  >
                    {getSeverityLabel(item.severity)}
                  </span>
                )}
                <span className={`text-gray-400 text-xs transition-transform ${isOpen ? "rotate-180" : ""}`}>▼</span>
              </button>
              {isOpen && result && (
                <div className="px-4 pb-4 pt-0 text-sm text-gray-700 border-t border-gray-50 space-y-2">
                  {/* Photo diagnosis results */}
                  {result.description && (
                    <div><span className="font-medium text-gray-500">{t("historyDescription")}</span> {result.description}</div>
                  )}
                  {result.recommendation && (
                    <div><span className="font-medium text-gray-500">{t("historyRecommendation")}</span> {result.recommendation}</div>
                  )}
                  {result.confidence != null && (
                    <div><span className="font-medium text-gray-500">{t("historyConfidence")}</span> {Math.round(result.confidence * 100)}%</div>
                  )}
                  {/* Lab results */}
                  {result.summary && (
                    <div><span className="font-medium text-gray-500">{t("historySummary")}</span> {result.summary}</div>
                  )}
                  {result.anomalies && result.anomalies.length > 0 && (
                    <div>
                      <span className="font-medium text-gray-500">{t("historyAnomalies")}</span>
                      <ul className="list-disc list-inside mt-1">
                        {result.anomalies.map((a, j) => (
                          <li key={j}>{typeof a === "string" ? a : a.name || JSON.stringify(a)}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
