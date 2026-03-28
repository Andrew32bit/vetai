# App Builder Skill — Telegram Mini App, iOS, Android

## Trigger
Use this skill when creating UI screens, components, flows, or full applications for:
- Telegram Mini App (React + @twa-dev/sdk)
- iOS (React Native / Swift UI)
- Android (React Native / Kotlin Compose)
- Cross-platform (React Native / Flutter)

Trigger keywords: "экран", "страница", "компонент", "UI", "дизайн", "приложение", "mini app", "мобильное", "интерфейс", "кнопка", "форма", "навигация"

## Design System — VetAI

### Brand
- Primary: #2AABEE (Telegram Blue)
- Success: #4CAF50
- Warning: #FF9800
- Danger: #F44336
- Background: var(--tg-theme-bg-color, #FFFFFF)
- Text: var(--tg-theme-text-color, #000000)
- Hint: var(--tg-theme-hint-color, #999999)

### Typography
- Headings: SF Pro Display / Inter, bold
- Body: SF Pro Text / Inter, regular
- Font sizes: 24/20/16/14/12px hierarchy

### Spacing & Radius
- Base unit: 4px
- Card padding: 16px
- Screen padding: 16-20px horizontal
- Border radius: cards 16-20px, buttons 12px, inputs 12px, chips 20px

### Component Patterns

#### Cards
```jsx
<div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4">
  <div className="flex items-center gap-3">
    <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center">
      <Icon size={24} className="text-tg-blue" />
    </div>
    <div>
      <div className="font-semibold">Title</div>
      <div className="text-sm text-gray-400">Description</div>
    </div>
  </div>
</div>
```

#### Buttons
```jsx
// Primary
<button className="w-full bg-tg-blue text-white font-semibold py-3 rounded-xl">
  Action
</button>

// Secondary
<button className="w-full border-2 border-tg-blue text-tg-blue font-semibold py-3 rounded-xl">
  Secondary
</button>

// Danger
<button className="w-full bg-red-500 text-white font-semibold py-3 rounded-xl">
  Delete
</button>
```

#### Bottom Navigation
- 5 tabs max
- Active: tg-blue color, bold icon
- Inactive: gray-400
- Icons from lucide-react, size 22
- Label font: 10px

#### Chat Bubbles
```jsx
// User message — right, blue bg, rounded-br-sm
// Bot message — left, gray-100 bg, rounded-bl-sm
// Max width: 80%
// Padding: px-4 py-2.5
// Font: text-sm leading-relaxed
```

#### Result/Diagnosis Cards
```jsx
// Severity badge: rounded-full px-2 py-1
// high → bg-red-100 text-red-600 "Срочно"
// medium → bg-yellow-100 text-yellow-700 "Внимание"
// low → bg-green-100 text-green-600 "Норма"
```

### Telegram Mini App Rules
1. ALWAYS call `WebApp.ready()` and `WebApp.expand()` on mount
2. Use Telegram theme CSS variables (--tg-theme-*)
3. Support safe-area-inset for notch devices
4. Use `WebApp.MainButton` for primary CTA when appropriate
5. Use `WebApp.BackButton` for navigation back
6. Haptic feedback: `WebApp.HapticFeedback.impactOccurred('medium')`
7. Close: `WebApp.close()` — only when flow is complete
8. Payments: `WebApp.openInvoice(url)` for Telegram Stars

### React Native / Mobile Rules
1. Use React Navigation for routing
2. SafeAreaView for all screens
3. Platform.select() for iOS/Android differences
4. Dimensions API for responsive sizing
5. KeyboardAvoidingView for forms
6. FlatList (not ScrollView) for long lists
7. AsyncStorage for local persistence
8. Image optimization: use resizeMode, cache headers

### Screen Architecture (always follow)
```
screens/
├── auth/
│   ├── OnboardingScreen.jsx   — welcome + pet type + details + plan
│   └── LoginScreen.jsx        — Telegram auth fallback
├── main/
│   ├── HomeScreen.jsx          — dashboard with action cards
│   ├── PhotoUploadScreen.jsx   — camera/gallery → AI analysis
│   ├── LabResultsScreen.jsx    — file upload → OCR → interpretation
│   ├── ChatScreen.jsx          — symptom chat with AI
│   └── HistoryScreen.jsx       — past diagnoses timeline
├── profile/
│   ├── ProfileScreen.jsx       — user + pet info
│   └── SubscriptionScreen.jsx  — plans, payment
└── shared/
    ├── LoadingScreen.jsx
    └── ErrorScreen.jsx
```

### Animation Guidelines
- Page transitions: slide from right (300ms ease)
- Cards: fade-in + translateY(10px → 0) on mount
- Loading: skeleton shimmer or Loader2 spin
- Buttons: scale(0.97) on press
- Success: checkmark lottie or simple scale bounce

### Accessibility
- All images: alt text in Russian
- Touch targets: minimum 44x44px
- Color contrast: WCAG AA minimum
- Font scaling: respect system settings
- Screen reader: aria-label on icons

### File Creation Checklist
When creating a new screen or component:
1. Import necessary hooks (useState, useEffect, useRef)
2. Import icons from lucide-react
3. Use Tailwind classes (frontend) or StyleSheet.create (React Native)
4. Add loading states
5. Add error handling with user-friendly Russian messages
6. Add empty states with illustrations
7. Connect to API with proper headers (x-telegram-id)
8. Test both light and dark themes