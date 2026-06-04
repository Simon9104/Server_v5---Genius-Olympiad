import * as Notifications from 'expo-notifications';
import * as BackgroundFetch from 'expo-background-fetch';
import * as TaskManager from 'expo-task-manager';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { fetchAlerts } from './api';

const BACKGROUND_FETCH_TASK = 'GREENIOT_ALERT_CHECK';
const LAST_ALERT_COUNT_KEY = 'lastAlertCount';
const SERVER_IP_KEY = 'serverIp';

// Configure how notifications are presented when the app is in the foreground
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

/**
 * Request notification permissions from the OS.
 * Returns the permission status object.
 */
export async function requestPermissions() {
  const { status: existingStatus } = await Notifications.getPermissionsAsync();

  if (existingStatus === 'granted') {
    return existingStatus;
  }

  const { status } = await Notifications.requestPermissionsAsync({
    ios: {
      allowAlert: true,
      allowBadge: true,
      allowSound: true,
    },
  });

  return status;
}

/**
 * Show an immediate local notification.
 * @param {string} title
 * @param {string} body
 */
export async function scheduleLocalNotification(title, body) {
  await Notifications.scheduleNotificationAsync({
    content: {
      title,
      body,
      sound: true,
    },
    trigger: null, // fire immediately
  });
}

/**
 * Define the background fetch task.
 * This must be called at the module level (outside of any component).
 */
TaskManager.defineTask(BACKGROUND_FETCH_TASK, async () => {
  try {
    const baseUrl = await AsyncStorage.getItem(SERVER_IP_KEY);
    if (!baseUrl) {
      return BackgroundFetch.BackgroundFetchResult.NoData;
    }

    const fullUrl = `http://${baseUrl}:8080`;
    const alerts = await fetchAlerts(fullUrl);

    if (!Array.isArray(alerts)) {
      return BackgroundFetch.BackgroundFetchResult.Failed;
    }

    const storedCountStr = await AsyncStorage.getItem(LAST_ALERT_COUNT_KEY);
    const lastCount = storedCountStr ? parseInt(storedCountStr, 10) : 0;
    const currentCount = alerts.length;

    if (currentCount > lastCount) {
      const newAlerts = alerts.slice(lastCount);
      for (const alert of newAlerts) {
        await scheduleLocalNotification('GreenIOT Alert', alert.msg || 'A new alert was received.');
      }
      await AsyncStorage.setItem(LAST_ALERT_COUNT_KEY, String(currentCount));
      return BackgroundFetch.BackgroundFetchResult.NewData;
    }

    return BackgroundFetch.BackgroundFetchResult.NoData;
  } catch (error) {
    console.error('[BackgroundFetch] Error:', error);
    return BackgroundFetch.BackgroundFetchResult.Failed;
  }
});

/**
 * Register the background fetch task that checks for new alerts every 15 minutes.
 * @param {string} baseUrl  — stored for use inside the task
 */
export async function setupBackgroundFetch(baseUrl) {
  // Persist the base IP so the background task can read it
  if (baseUrl) {
    const ip = baseUrl.replace(/^https?:\/\//, '').replace(/:8080$/, '');
    await AsyncStorage.setItem(SERVER_IP_KEY, ip);
  }

  try {
    const isRegistered = await TaskManager.isTaskRegisteredAsync(BACKGROUND_FETCH_TASK);

    if (!isRegistered) {
      await BackgroundFetch.registerTaskAsync(BACKGROUND_FETCH_TASK, {
        minimumInterval: 15 * 60, // 15 minutes in seconds
        stopOnTerminate: false,
        startOnBoot: true,
      });
    }
  } catch (error) {
    console.warn('[setupBackgroundFetch] Could not register task:', error.message);
  }
}
