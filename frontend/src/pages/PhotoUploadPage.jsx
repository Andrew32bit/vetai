import { useState, useRef } from "react";
import { Camera, Image, Upload, Loader2 } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function PhotoUploadPage() {
  const [photo, setPhoto] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const fileRef = useRef();
  const cameraRef = useRef();

  const handleFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setPhoto(file);
    setPreview(URL.createObjectURL(file));
    setResult(null);
  };

  const [limitError, setLimitError] = useState(null);

  const analyze = async () => {
    if (!photo) return;
    setLoading(true);
    setLimitError(null);
    try {
      const telegramId = localStorage.getItem("vetai_telegram_id") || "12345";
      const form = new FormData();
      form.append("photo", photo);

      const res = await fetch(`${API_URL}/api/v1/diagnosis/photo`, {
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
      <h1 className="text-xl font-bold mb-4 text-gray-900">Проверка по фото 📸</h1>
      <p className="text-sm text-gray-600 mb-6">
        Сфотографируйте проблемное место питомца. AI определит возможное заболевание.
      </p>

      {/* Upload area */}
      {!preview ? (
        <div className="flex gap-3">
          <button
            onClick={() => cameraRef.current.click()}
            className="flex-1 h-40 border-2 border-dashed border-gray-300 rounded-2xl flex flex-col items-center justify-center gap-3 text-gray-400 hover:border-tg-blue hover:text-tg-blue transition-colors"
          >
            <Camera size={36} />
            <span className="font-medium text-sm">Камера</span>
          </button>
          <button
            onClick={() => fileRef.current.click()}
            className="flex-1 h-40 border-2 border-dashed border-gray-300 rounded-2xl flex flex-col items-center justify-center gap-3 text-gray-400 hover:border-tg-blue hover:text-tg-blue transition-colors"
          >
            <Image size={36} />
            <span className="font-medium text-sm">Галерея</span>
          </button>
        </div>
      ) : (
        <div className="relative">
          <img
            src={preview}
            alt="Pet photo"
            className="w-full h-48 object-cover rounded-2xl"
          />
          <button
            onClick={() => { setPreview(null); setPhoto(null); setResult(null); }}
            className="absolute top-2 right-2 bg-black/50 text-white w-8 h-8 rounded-full flex items-center justify-center"
          >
            ✕
          </button>
        </div>
      )}

      <input
        ref={cameraRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleFile}
        className="hidden"
      />
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        onChange={handleFile}
        className="hidden"
      />

      {preview && !result && (
        <button
          onClick={analyze}
          disabled={loading}
          className="w-full mt-4 bg-tg-blue text-white font-semibold py-3 rounded-xl flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? <Loader2 className="animate-spin" size={20} /> : <Upload size={20} />}
          {loading ? "Анализируем..." : "Проверить"}
        </button>
      )}

      {/* Limit error */}
      {limitError && (
        <div className="mt-4 p-4 rounded-2xl bg-red-50 border border-red-200 text-center text-sm text-red-600 font-medium">
          {limitError}
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="mt-4 p-4 rounded-2xl bg-white border border-gray-100 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="font-bold text-lg text-gray-900">{result.condition}</span>
            <span
              className={`text-xs font-semibold px-2 py-1 rounded-full ${
                result.severity === "high"
                  ? "bg-red-100 text-red-600"
                  : result.severity === "medium"
                  ? "bg-yellow-100 text-yellow-700"
                  : "bg-green-100 text-green-600"
              }`}
            >
              {result.severity === "high" ? "Срочно" : result.severity === "medium" ? "Внимание" : "Норма"}
            </span>
          </div>
          <p className="text-sm text-gray-600 mb-3">{result.description}</p>
          <p className="text-sm font-medium text-tg-blue">{result.recommendation}</p>
          <div className="mt-3 text-xs text-gray-400">
            Уверенность: {Math.round(result.confidence * 100)}%
          </div>
        </div>
      )}
    </div>
  );
}