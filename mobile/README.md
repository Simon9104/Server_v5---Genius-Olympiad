# GreenIOT Mobile App

React Native / Expo app for monitoring the GreenIOT greenhouse system.

## Prerequisites

- Node.js 18+
- npm or yarn
- [Expo Go](https://expo.dev/go) on your Android/iOS device (for development)
- EAS CLI for building a production APK (optional)

## Getting started

```bash
# 1. Install dependencies
cd mobile && npm install

# 2. Start the Expo dev server
npx expo start
```

Scan the QR code with the Expo Go app to run it on your phone, or press `a` to open an Android emulator.

## Building an APK

You can build a standalone APK using EAS (Expo Application Services):

```bash
# Install EAS CLI (once, globally)
npm install -g eas-cli

# Log in to your Expo account
eas login

# Build a preview APK for Android
npx eas build -p android --profile preview
```

Alternatively, use the classic Expo build service:

```bash
npx expo build:android
```

## Configuration

On first launch, go to **Settings** and enter the IP address of the machine running the GreenIOT server (port 8080 is used automatically). Tap **Save**, then go to **Dashboard** and tap **Connect**.

## Project structure

```
mobile/
  App.js                      Entry point
  app.json                    Expo configuration
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
      api.js                  Typed fetch helpers
      notifications.js        Local notifications + background fetch
    navigation/
      AppNavigator.js         Bottom tab navigator
```

## License

© 2024 GreenIOT. All rights reserved.
