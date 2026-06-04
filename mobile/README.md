# GreenIOT Mobile App

React Native / Expo app for monitoring the GreenIOT greenhouse system.
Runs on **Android** and **iPhone / iPad** from a single codebase.

## Prerequisites

- Node.js 18+
- npm or yarn
- [Expo Go](https://expo.dev/go) on your device (for development)
- EAS CLI for building production binaries
- **iOS only:** Apple Developer account ($99/year) required for device builds

## Getting started

```bash
cd mobile && npm install
npx expo start
```

Scan the QR code with Expo Go to run on your phone, or press `a` for Android emulator / `i` for iOS simulator.

## Building — Android APK

```bash
# Install EAS CLI once globally
npm install -g eas-cli

# Log in (headless / SSH — use an access token from expo.dev)
export EXPO_TOKEN=your_token_here

# Build preview APK
eas build -p android --profile preview
```

Download the `.apk` from the link EAS prints, then sideload it on your device.

## Building — iOS / iPadOS (TestFlight beta)

```bash
export EXPO_TOKEN=your_token_here

# Build an ad-hoc IPA for registered devices
eas build -p ios --profile preview

# — OR — build for TestFlight / App Store
eas build -p ios --profile production
```

> **Note:** iOS builds require your Apple Developer Team ID.
> EAS will prompt you for it on first run and handle provisioning profiles automatically.
> Once the build is complete, submit to TestFlight:
> ```bash
> eas submit -p ios --latest
> ```

## iOS simulator build (no Apple account needed)

```bash
eas build -p ios --profile preview-simulator
```

This produces a `.app` bundle you can drag into the Xcode simulator.

## Configuration

On first launch open **Settings**, enter the IP address of the machine running
`server.py` (port 8080 is used automatically), and tap **Save**.
Then go to **Dashboard** → **Connect**.

## Project structure

```
mobile/
  App.js                      Entry point
  app.json                    Expo config (Android + iOS)
  eas.json                    Build profiles
  package.json
  src/
    screens/
      DashboardScreen.js      Live sensor data + door controls
      AlertsScreen.js         ThingSpeak failure event log
      SettingsScreen.js       IP, poll interval, notifications
    components/
      PicoCard.js             Per-Pico sensor card
      DoorControls.js         Open / Close / Auto buttons
      SensorBar.js            Horizontal progress bar
      AlertItem.js            Single alert row
    hooks/
      usePolling.js           Foreground polling hook
    utils/
      api.js                  Fetch helpers
      notifications.js        Local notifications + background fetch
    navigation/
      AppNavigator.js         Bottom tab navigator
```

## License

© 2026 Simon Onderisin — GreenIOT. All rights reserved.
