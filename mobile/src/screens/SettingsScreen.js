import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  ScrollView,
  Alert,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { requestPermissions } from '../utils/notifications';

const SERVER_IP_KEY = 'serverIp';
const POLL_INTERVAL_KEY = 'pollInterval';

const POLL_OPTIONS = [
  { label: '5 s', value: 5000 },
  { label: '10 s', value: 10000 },
  { label: '30 s', value: 30000 },
];

export default function SettingsScreen() {
  const [ipInput, setIpInput] = useState('');
  const [savedMessage, setSavedMessage] = useState('');
  const [pollInterval, setPollInterval] = useState(5000);

  useEffect(() => {
    async function loadSettings() {
      const ip = await AsyncStorage.getItem(SERVER_IP_KEY);
      const interval = await AsyncStorage.getItem(POLL_INTERVAL_KEY);
      if (ip) setIpInput(ip);
      if (interval) setPollInterval(parseInt(interval, 10));
    }
    loadSettings();
  }, []);

  async function handleSaveIp() {
    const trimmed = ipInput.trim();
    if (!trimmed) return;
    await AsyncStorage.setItem(SERVER_IP_KEY, trimmed);
    setSavedMessage('Saved!');
    setTimeout(() => setSavedMessage(''), 2000);
  }

  async function handleSelectInterval(value) {
    setPollInterval(value);
    await AsyncStorage.setItem(POLL_INTERVAL_KEY, String(value));
  }

  async function handleRequestPermissions() {
    const status = await requestPermissions();
    if (status === 'granted') {
      Alert.alert('Permissions', 'Notification permission granted.');
    } else {
      Alert.alert(
        'Permissions',
        `Notification permission status: ${status}. Please enable notifications in your device settings.`
      );
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="light-content" backgroundColor="#0f0f1a" />
      <ScrollView style={styles.scroll} contentContainerStyle={styles.content}>
        <Text style={styles.pageTitle}>Settings</Text>

        {/* Server IP */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Server IP Address</Text>
          <TextInput
            style={styles.input}
            value={ipInput}
            onChangeText={setIpInput}
            placeholder="e.g. 192.168.1.10"
            placeholderTextColor="#555"
            keyboardType="numeric"
            autoCapitalize="none"
            autoCorrect={false}
          />
          <TouchableOpacity style={styles.saveBtn} onPress={handleSaveIp} activeOpacity={0.75}>
            <Text style={styles.saveBtnText}>Save</Text>
          </TouchableOpacity>
          {savedMessage ? (
            <Text style={styles.savedMsg}>{savedMessage}</Text>
          ) : null}
        </View>

        {/* Poll interval */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Poll Interval</Text>
          <View style={styles.optionRow}>
            {POLL_OPTIONS.map((opt) => (
              <TouchableOpacity
                key={opt.value}
                style={[
                  styles.optionBtn,
                  pollInterval === opt.value ? styles.optionBtnActive : null,
                ]}
                onPress={() => handleSelectInterval(opt.value)}
                activeOpacity={0.75}
              >
                <Text
                  style={[
                    styles.optionBtnText,
                    pollInterval === opt.value ? styles.optionBtnTextActive : null,
                  ]}
                >
                  {opt.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Notifications */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notifications</Text>
          <TouchableOpacity
            style={styles.notifBtn}
            onPress={handleRequestPermissions}
            activeOpacity={0.75}
          >
            <Text style={styles.notifBtnText}>Request Notification Permission</Text>
          </TouchableOpacity>
        </View>

        {/* About */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About</Text>
          <Text style={styles.aboutText}>GreenIOT Monitor</Text>
          <Text style={styles.aboutMuted}>Version 1.0.0</Text>
          <Text style={styles.aboutMuted}>© 2024 GreenIOT. All rights reserved.</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: '#0f0f1a',
  },
  scroll: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 16,
    paddingBottom: 40,
  },
  pageTitle: {
    color: '#fff',
    fontSize: 22,
    fontWeight: '700',
    marginTop: 20,
    marginBottom: 20,
  },
  section: {
    backgroundColor: '#1e1e2e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  sectionTitle: {
    color: '#aaa',
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 12,
  },
  input: {
    backgroundColor: '#0f0f1a',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#2a2a3e',
    color: '#fff',
    fontSize: 15,
    paddingHorizontal: 12,
    paddingVertical: 9,
    marginBottom: 10,
  },
  saveBtn: {
    backgroundColor: '#166534',
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#4ade80',
  },
  saveBtnText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 14,
  },
  savedMsg: {
    color: '#4ade80',
    textAlign: 'center',
    marginTop: 8,
    fontSize: 13,
  },
  optionRow: {
    flexDirection: 'row',
    gap: 10,
  },
  optionBtn: {
    flex: 1,
    paddingVertical: 9,
    borderRadius: 8,
    alignItems: 'center',
    backgroundColor: '#0f0f1a',
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  optionBtnActive: {
    backgroundColor: '#14532d',
    borderColor: '#4ade80',
  },
  optionBtnText: {
    color: '#666',
    fontWeight: '600',
    fontSize: 14,
  },
  optionBtnTextActive: {
    color: '#4ade80',
  },
  notifBtn: {
    backgroundColor: '#1e3a5f',
    borderRadius: 8,
    paddingVertical: 11,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#60a5fa',
  },
  notifBtnText: {
    color: '#60a5fa',
    fontWeight: '600',
    fontSize: 14,
  },
  aboutText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 4,
  },
  aboutMuted: {
    color: '#666',
    fontSize: 13,
    marginBottom: 2,
  },
});
