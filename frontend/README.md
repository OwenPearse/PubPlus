# PubPlus frontend

Minimal Expo (SDK 54) + React Native app for staged Discovery / Home / Search work.

## Prerequisites

- Node.js (LTS recommended)
- For devices: Expo Go, or Android Studio / Xcode as usual for native runs

## Setup

```bash
cd frontend
npm install
```

## Run

```bash
npm start          # Expo dev server
npm run android
npm run ios        # macOS only for local iOS builds
npm run web
```

## Tests

```bash
npm test
```

Uses Jest with the `jest-expo` preset and React Native Testing Library.
