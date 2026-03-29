import { useState, useRef } from "react";
import { FileText, Upload, Loader2 } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function LabResultsPage() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const fileRef = useRef();

  const handleFile = (e) => {
    const f = e.target.files[0];
    if (f) { setFile(f); setResult(null); }
  };

  const [limitError, setLimitError] = useState(null);

  const analyze = async () => {
    if (!file) return;
    setLoading(true);
    setLimitError(null);
    try {
      const telegramId = localStorage.getItem("vetai_telegram_id") || "12345";
      const form = new FormData();
      form.append("file", file);

      const res = await fetch(`${API_URL}/api/v1/diagnosis/lab-results`, {
        method: "POST",
        headers: { "x-telegram-id": telegramId },
        body: form,
      });

      if (res.status === 429) {
        setLimitError("Лимит 3 запроса в день исчерпан. Попробуйте завтра.");
        return;
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="px-4 py-6">
      <h1 className="text-xl font-bold mb-4 text-gray-900">Загрузить анализы 📋</h1>
      <p className="text-sm text-gray-600 mb-6">
        Загрузите изображение или PDF. AI распознает текст и найдёт отклонения.
      </p>

      <button
        onClick={() => fileRef.current.click()}
        className="w-full h-32 border-2 border-dashed border-gray-300 rounded-2xl flex flex-col items-center justify-center gap-2 text-gray-400 hover:border-tg-blue transition-colors"
      >
        <FileText size={32} />
        <span className="font-medium text-sm">
          {file ? file.name : "Фото или PDF анализов"}
        </span>
      </button>

      <input
        ref={fileRef}
        type="file"
        accept="image/*,.pdf"
        onChange={handleFile}
        className="hidden"
      />

      {file && !result && (
        <button
          onClick={analyze}
          disabled={loading}
          className="w-full mt-4 bg-tg-blue text-white font-semibold py-3 rounded-xl flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? <Loader2 className="animate-spin" size={20} /> : <Upload size={20} />}
          {loading ? "Распознаём..." : "Расшифровать"}
        </button>
      )}

      {/* Limit error */}
      {limitError && (
        <div className="mt-4 p-4 rounded-2xl bg-red-50 border border-red-200 text-center text-sm text-red-600 font-medium">
          {limitError}
        </div>
      )}

      {result && (
        <div className="mt-4 space-y-3">
          {result.anomalies?.length > 0 && (
            <div className="p-4 rounded-2xl bg-red-50 border border-red-100">
              <div className="font-bold text-red-600 mb-2">Отклонения</div>
              {result.anomalies.map((a, i) => (
                <div key={i} className="text-sm text-red-700">• {a}</div>
              ))}
            </div>
          )}

          {result.diagnosis && (
            <div className="p-4 rounded-2xl bg-yellow-50 border border-yellow-200">
              <div className="font-bold text-yellow-700 mb-2">Предварительный диагноз</div>
              <div className="text-sm text-gray-700">{result.diagnosis}</div>
            </div>
          )}

          <div className="p-4 rounded-2xl bg-blue-50 border border-blue-100">
            <div className="font-bold text-tg-blue mb-2">Заключение AI</div>
            <div className="text-sm text-gray-700">{result.summary}</div>
          </div>

          <div className="text-xs text-gray-400 text-center px-4">
            Результаты AI носят предварительный характер. Обратитесь к ветеринарному врачу для точного диагноза.
          </div>
        </div>
      )}
    </div>
  );
}