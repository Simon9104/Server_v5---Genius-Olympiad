import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { sendDoor } from '../utils/api';

/**
 * DoorControls — three door-command buttons for one Pico.
 *
 * Props:
 *   picoId    {number}    — 1 | 2 | 3
 *   baseUrl   {string}    — e.g. "http://192.168.1.10:8080"
 *   onSuccess {function}  — called after a successful command
 */
export default function DoorControls({ picoId, baseUrl, onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [lastError, setLastError] = useState(null);

  async function handleCommand(value) {
    if (!baseUrl || loading) return;
    setLoading(true);
    setLastError(null);
    try {
      await sendDoor(baseUrl, picoId, value);
      if (onSuccess) onSuccess();
    } catch (err) {
      setLastError(err.message || 'Command failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.container}>
      {loading ? (
        <ActivityIndicator color="#4ade80" size="small" />
      ) : (
        <View style={styles.row}>
          <TouchableOpacity
            style={[styles.btn, styles.btnOpen]}
            onPress={() => handleCommand(1)}
            activeOpacity={0.75}
          >
            <Text style={styles.btnText}>Open</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.btn, styles.btnClose]}
            onPress={() => handleCommand(0)}
            activeOpacity={0.75}
          >
            <Text style={styles.btnText}>Close</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.btn, styles.btnAuto]}
            onPress={() => handleCommand(null)}
            activeOpacity={0.75}
          >
            <Text style={styles.btnText}>Auto</Text>
          </TouchableOpacity>
        </View>
      )}

      {lastError ? (
        <Text style={styles.errorText}>{lastError}</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 8,
  },
  row: {
    flexDirection: 'row',
    gap: 8,
  },
  btn: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnOpen: {
    backgroundColor: '#166534', // dark green
    borderWidth: 1,
    borderColor: '#4ade80',
  },
  btnClose: {
    backgroundColor: '#7f1d1d', // dark red
    borderWidth: 1,
    borderColor: '#f87171',
  },
  btnAuto: {
    backgroundColor: '#1e3a5f', // dark blue
    borderWidth: 1,
    borderColor: '#60a5fa',
  },
  btnText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
  errorText: {
    color: '#f87171',
    fontSize: 12,
    marginTop: 6,
    textAlign: 'center',
  },
});
