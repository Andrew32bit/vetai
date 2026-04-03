/**
 * Bilingual support: Russian (default) + English.
 * Language detected from Telegram WebApp.initDataUnsafe.user.language_code.
 */

const translations = {
  ru: {
    // App
    connecting: "Podklyuchaemsya...",
    connectingDisplay: "Подключаемся...",

    // HomePage
    greeting: "Привет",
    healthQuestion: "Как здоровье вашего питомца?",
    betaBanner: "Бета — бесплатно! Использовано:",
    photoCheckTitle: "Проверка по фото",
    photoCheckDesc: "Сфотографируйте проблемную область",
    labUploadTitle: "Анализы и УЗИ",
    labUploadDesc: "AI расшифрует анализы, УЗИ, рентген",
    symptomChatTitle: "Описать симптомы",
    symptomChatDesc: "Чат с AI-ветеринаром",
    dailyTipTitle: "Совет дня",
    dailyTipText: "Регулярно проверяйте уши питомца — покраснение или запах могут указывать на отит. Загрузите фото для быстрой проверки!",
    feedbackButton: "Оставить отзыв или предложение",
    feedbackTitle: "Обратная связь",
    feedbackPlaceholder: "Напишите ваш отзыв, вопрос или предложение...",
    feedbackSend: "Отправить",
    feedbackCancel: "Отмена",
    feedbackThanks: "Спасибо за отзыв!",

    // ChatPage
    chatTitle: "Чат с AI-ветеринаром",
    chatClear: "Очистить",
    chatInitialMessage: "Здравствуйте! Я AI-ветеринар VetAI. Опишите симптомы вашего питомца, и я помогу разобраться. Что вас беспокоит?",
    chatPlaceholder: "Опишите симптомы...",
    chatLimitExhausted: "Лимит 3 запроса в день исчерпан. Попробуйте завтра.",
    chatError: "Извините, произошла ошибка. Попробуйте ещё раз.",
    serverOverloaded: "Сейчас очень много пользователей! Мы срочно масштабируем серверы. Попробуйте через 5-10 минут — мы уже работаем над этим.",
    chatRecommendation: "Рекомендация",
    chatFindClinic: "Найти клинику на карте",

    // PhotoUploadPage
    photoTitle: "Проверка по фото",
    photoSubtitle: "Загрузите фото питомца, снимок УЗИ, рентген или МРТ. AI проанализирует и даст оценку.",
    photoUploadButton: "Загрузить фото / снимок",
    photoCameraOrGallery: "Камера, галерея или файл",
    photoComplaintPlaceholder: "Опишите проблему (необязательно)",
    photoAnalyzing: "Анализируем...",
    photoCheck: "Проверить",
    photoLimitExhausted: "Дневной лимит исчерпан. Попробуйте завтра.",
    photoNoAnimal: "Животное не найдено",
    photoNoAnimalDesc: "Пожалуйста, загрузите фото вашего питомца",
    photoUrgent: "Срочно",
    photoAttention: "Внимание",
    photoNormal: "Норма",
    photoConfidence: "Уверенность",
    // Hints
    hints: [
      "чешется", "рана", "опухоль/шишка", "выпадает шерсть",
      "покраснение", "гноится", "хромает", "отёк",
      "перхоть", "корки", "пятна", "облысение",
      "слезятся глаза", "воспаление уха", "неприятный запах",
      "появилось недавно", "не заживает", "увеличивается",
      "после еды", "после прогулки", "после укуса", "после купания",
      "снимок УЗИ", "рентген", "МРТ",
    ],

    // LabResultsPage
    labTitle: "Анализы и снимки",
    labSubtitle: "Загрузите фото анализов, УЗИ, рентген или МРТ. AI расшифрует и найдёт отклонения.",
    labFilePrompt: "Фото, PDF анализов или снимок УЗИ/рентген",
    labRecognizing: "Распознаём...",
    labDecode: "Расшифровать",
    labLimitExhausted: "Лимит 3 запроса в день исчерпан. Попробуйте завтра.",
    labAnomalies: "Отклонения",
    labDiagnosis: "Предварительный диагноз",
    labConclusion: "Заключение AI",
    labDisclaimer: "Результаты AI носят предварительный характер. Обратитесь к ветеринарному врачу для точного диагноза.",

    // HistoryPage
    historyTitle: "История проверок",
    historyLoading: "Загрузка...",
    historyEmpty: "Пока пусто",
    historyEmptyDesc: "Здесь будут сохраняться результаты проверок вашего питомца",
    historyPhoto: "Фото",
    historyLab: "Анализы",
    historyChat: "Чат",
    historyEmergency: "Экстренно",
    historyUrgent: "Срочно",
    historyAttention: "Внимание",
    historyNormal: "Норма",
    historyDescription: "Описание:",
    historyRecommendation: "Рекомендация:",
    historyConfidence: "Уверенность:",
    historySummary: "Итог:",
    historyAnomalies: "Отклонения:",

    // OnboardingPage
    onboardingWelcomeDesc: "AI-ветеринар в вашем телефоне. Проверьте здоровье питомца по фото, анализам или симптомам.",
    onboardingStart: "Начать",
    onboardingPetQuestion: "Кто ваш питомец?",
    onboardingCat: "Кошка",
    onboardingDog: "Собака",
    onboardingPetDetails: "Расскажите о питомце",
    onboardingPetName: "Имя питомца",
    onboardingBreed: "Порода (необязательно)",
    onboardingCity: "Ваш город (для поиска клиник)",
    onboardingNext: "Далее",
    onboardingBetaTitle: "Бета-версия — все функции бесплатны!",
    onboardingDailyLimit: "Дневной лимит:",
    onboardingDailyLimitDesc: "10 запросов в день (фото + чат + анализы)",
    onboardingBetaNote: "После завершения бета-тестирования будет введена платная подписка",
    onboardingStartUsing: "Начать использовать",
    onboardingDisclaimer: "VetAI не ставит диагнозы и не назначает лечение. Сервис даёт предварительную оценку и рекомендует консультацию специалиста.",

    // BottomNav
    navHome: "Главная",
    navPhoto: "Фото",
    navLab: "Анализы/УЗИ",
    navChat: "Чат",
    navHistory: "История",
  },

  en: {
    // App
    connecting: "Connecting...",
    connectingDisplay: "Connecting...",

    // HomePage
    greeting: "Hello",
    healthQuestion: "How is your pet feeling?",
    betaBanner: "Beta — free! Used:",
    photoCheckTitle: "Photo Check",
    photoCheckDesc: "Take a photo of the problem area",
    labUploadTitle: "Lab Results & Scans",
    labUploadDesc: "AI interprets labs, ultrasound, X-ray",
    symptomChatTitle: "Describe Symptoms",
    symptomChatDesc: "Chat with AI veterinarian",
    dailyTipTitle: "Daily Tip",
    dailyTipText: "Regularly check your pet's ears — redness or odor may indicate otitis. Upload a photo for a quick check!",
    feedbackButton: "Leave feedback or suggestion",
    feedbackTitle: "Feedback",
    feedbackPlaceholder: "Write your feedback, question, or suggestion...",
    feedbackSend: "Send",
    feedbackCancel: "Cancel",
    feedbackThanks: "Thank you for your feedback!",

    // ChatPage
    chatTitle: "AI Vet Chat",
    chatClear: "Clear",
    chatInitialMessage: "Hello! I'm VetAI, your AI veterinarian. Describe your pet's symptoms and I'll help you figure it out. What concerns you?",
    chatPlaceholder: "Describe symptoms...",
    chatLimitExhausted: "Daily limit of 3 requests exhausted. Try again tomorrow.",
    chatError: "Sorry, an error occurred. Please try again.",
    serverOverloaded: "We're experiencing high demand right now! We're scaling up our servers. Please try again in 5-10 minutes — we're on it!",
    chatRecommendation: "Recommendation",
    chatFindClinic: "Find a clinic on the map",

    // PhotoUploadPage
    photoTitle: "Photo Check",
    photoSubtitle: "Upload a pet photo, ultrasound, X-ray, or MRI scan. AI will analyze and assess.",
    photoUploadButton: "Upload Photo / Scan",
    photoCameraOrGallery: "Camera, gallery, or file",
    photoComplaintPlaceholder: "Describe the problem (optional)",
    photoAnalyzing: "Analyzing...",
    photoCheck: "Check",
    photoLimitExhausted: "Daily limit exhausted. Try again tomorrow.",
    photoNoAnimal: "No animal found",
    photoNoAnimalDesc: "Please upload a photo of your pet",
    photoUrgent: "Urgent",
    photoAttention: "Attention",
    photoNormal: "Normal",
    photoConfidence: "Confidence",
    // Hints
    hints: [
      "itching", "wound", "lump/bump", "hair loss",
      "redness", "discharge", "limping", "swelling",
      "dandruff", "scabs", "spots", "bald patches",
      "watery eyes", "ear inflammation", "bad smell",
      "appeared recently", "not healing", "getting bigger",
      "after eating", "after a walk", "after a bite", "after bathing",
      "ultrasound", "X-ray", "MRI",
    ],

    // LabResultsPage
    labTitle: "Lab Results & Scans",
    labSubtitle: "Upload lab results, ultrasound, X-ray, or MRI. AI will interpret and find anomalies.",
    labFilePrompt: "Photo, PDF of lab results or ultrasound/X-ray scan",
    labRecognizing: "Recognizing...",
    labDecode: "Interpret",
    labLimitExhausted: "Daily limit of 3 requests exhausted. Try again tomorrow.",
    labAnomalies: "Anomalies",
    labDiagnosis: "Preliminary Diagnosis",
    labConclusion: "AI Conclusion",
    labDisclaimer: "AI results are preliminary. Consult a veterinarian for an accurate diagnosis.",

    // HistoryPage
    historyTitle: "Check History",
    historyLoading: "Loading...",
    historyEmpty: "Nothing yet",
    historyEmptyDesc: "Your pet's check results will be saved here",
    historyPhoto: "Photo",
    historyLab: "Lab Results",
    historyChat: "Chat",
    historyEmergency: "Emergency",
    historyUrgent: "Urgent",
    historyAttention: "Attention",
    historyNormal: "Normal",
    historyDescription: "Description:",
    historyRecommendation: "Recommendation:",
    historyConfidence: "Confidence:",
    historySummary: "Summary:",
    historyAnomalies: "Anomalies:",

    // OnboardingPage
    onboardingWelcomeDesc: "AI veterinarian in your phone. Check your pet's health with a photo, lab results, or symptoms.",
    onboardingStart: "Get Started",
    onboardingPetQuestion: "What is your pet?",
    onboardingCat: "Cat",
    onboardingDog: "Dog",
    onboardingPetDetails: "Tell us about your pet",
    onboardingPetName: "Pet name",
    onboardingBreed: "Breed (optional)",
    onboardingCity: "Your city (for finding clinics)",
    onboardingNext: "Next",
    onboardingBetaTitle: "Beta — all features are free!",
    onboardingDailyLimit: "Daily limit:",
    onboardingDailyLimitDesc: "10 requests per day (photo + chat + lab results)",
    onboardingBetaNote: "A paid subscription will be introduced after the beta period ends",
    onboardingStartUsing: "Start Using",
    onboardingDisclaimer: "VetAI does not diagnose or prescribe treatment. The service provides a preliminary assessment and recommends consulting a specialist.",

    // BottomNav
    navHome: "Home",
    navPhoto: "Photo",
    navLab: "Lab/Scans",
    navChat: "Chat",
    navHistory: "History",
  },
};

/**
 * Get the current language from localStorage.
 * @returns {"ru" | "en"}
 */
export function getLang() {
  return localStorage.getItem("vetai_language") || "ru";
}

/**
 * Get a translation string by key.
 * @param {string} key
 * @returns {string}
 */
export function t(key) {
  const lang = getLang();
  return translations[lang]?.[key] ?? translations.ru[key] ?? key;
}

export default translations;
