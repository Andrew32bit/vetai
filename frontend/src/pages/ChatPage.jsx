import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Loader2, MapPin, Trash2, ThumbsUp, ThumbsDown } from "lucide-react";
import { t, getLang } from "../i18n";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const STORAGE_KEY = "vetai_chat_messages";

function getInitialMessages() {
  return [
    {
      role: "assistant",
      content: t("chatInitialMessage"),
    },
  ];
}

export default function ChatPage() {
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch {}
    return getInitialMessages();
  });
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [reactions, setReactions] = useState({});
  const scrollRef = useRef();

  const sendReaction = async (msgIndex, reaction, messageText) => {
    setReactions((prev) => ({ ...prev, [msgIndex]: reaction }));
    try {
      const telegramId = localStorage.getItem("vetai_telegram_id") || "12345";
      await fetch(`${API_URL}/api/v1/chat/feedback?reaction=${reaction}&message_text=${encodeURIComponent(messageText.substring(0, 200))}`, {
        method: "POST",
        headers: { "x-telegram-id": telegramId },
      });
    } catch (err) {
      console.error("Feedback error:", err);
    }
  };

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  const clearChat = useCallback(() => {
    const initial = getInitialMessages();
    setMessages(initial);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const user = JSON.parse(localStorage.getItem("vetai_user") || "{}");

      const telegramId = localStorage.getItem("vetai_telegram_id") || "12345";
      const language = getLang();

      const res = await fetch(`${API_URL}/api/v1/chat/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-telegram-id": telegramId,
        },
        body: JSON.stringify({
          message: userMsg.content,
          history: messages
            .filter((m) => m.role === "user" || m.role === "assistant")
            .map((m) => ({ role: m.role, content: m.content })),
          city: user.city || null,
          language,
        }),
      });

      if (res.status === 429) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: t("chatLimitExhausted") },
        ]);
        return;
      }

      const data = await res.json();

      // Add assistant reply
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);

      // If clinic recommendation exists, add it as a separate message
      if (data.clinic_recommendation) {
        setMessages((prev) => [
          ...prev,
          { role: "clinic", content: data.clinic_recommendation },
        ]);
      }
    } catch (err) {
      const isServerDown = err.message?.includes("Failed to fetch") || err.message?.includes("NetworkError") || err.message?.includes("503");
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: isServerDown ? t("serverOverloaded") : t("chatError") },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const renderMessage = (msg, i) => {
    if (msg.role === "clinic") {
      // Extract URL from the message
      const urlMatch = msg.content.match(/(https:\/\/(?:yandex\.ru\/maps|www\.google\.com\/maps)\/[^\s]+)/);
      const url = urlMatch ? urlMatch[1] : null;
      // Get text before URL, trim whitespace
      const beforeUrl = url ? msg.content.split(url)[0].replace(/\n+/g, ' ').trim() : msg.content.trim();

      return (
        <div key={i} className="flex justify-start">
          <div className="max-w-[85%] px-4 py-3 rounded-2xl rounded-bl-sm bg-red-50 border border-red-200 text-sm">
            <div className="flex items-center gap-2 text-red-600 font-semibold mb-1">
              <MapPin size={16} />
              {t("chatRecommendation")}
            </div>
            <div className="text-gray-700">
              {url ? (
                <>
                  <p className="mb-2">{beforeUrl}</p>
                  <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-tg-blue underline font-medium"
                  >
                    {t("chatFindClinic")}
                  </a>
                </>
              ) : (
                beforeUrl
              )}
            </div>
          </div>
        </div>
      );
    }

    const isBot = msg.role === "assistant" && i > 0;

    return (
      <div
        key={i}
        className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
      >
        <div className="max-w-[80%]">
          <div
            className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-line ${
              msg.role === "user"
                ? "bg-tg-blue text-white rounded-br-sm"
                : "bg-gray-100 text-gray-800 rounded-bl-sm"
            }`}
          >
            {msg.content}
          </div>
          {isBot && !reactions[i] && (
            <div className="flex gap-2 mt-1 ml-1">
              <button onClick={() => sendReaction(i, "like", msg.content)} className="text-gray-300 hover:text-green-500 transition-colors">
                <ThumbsUp size={14} />
              </button>
              <button onClick={() => sendReaction(i, "dislike", msg.content)} className="text-gray-300 hover:text-red-500 transition-colors">
                <ThumbsDown size={14} />
              </button>
            </div>
          )}
          {reactions[i] && (
            <div className="text-[10px] text-gray-300 mt-1 ml-1">
              {reactions[i] === "like" ? "👍" : "👎"}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with clear button */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200">
        <h1 className="text-lg font-bold text-gray-900">{t("chatTitle")}</h1>
        <button
          onClick={clearChat}
          className="flex items-center gap-1 text-sm text-gray-400 hover:text-red-500 transition-colors"
          title={t("chatClear")}
        >
          <Trash2 size={16} />
          <span>{t("chatClear")}</span>
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.map(renderMessage)}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-sm">
              <Loader2 className="animate-spin text-gray-400" size={18} />
            </div>
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 px-4 py-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder={t("chatPlaceholder")}
          className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 focus:border-tg-blue focus:outline-none text-sm"
        />
        <button
          onClick={sendMessage}
          disabled={!input.trim() || loading}
          className="bg-tg-blue text-white w-10 h-10 rounded-xl flex items-center justify-center disabled:opacity-50"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
