import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

/**
 * AlertItem — displays a single alert row.
 *
 * Props:
 *   alert  {{ time: string, msg: string }}
 */
export default function AlertItem({ alert }) {
  if (!alert) return null;

  return (
    <View style={styles.container}>
      <Text style={styles.time}>{alert.time || '—'}</Text>
      <Text style={styles.msg}>{alert.msg || 'Unknown alert'}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#1e1e2e',
    borderRadius: 10,
    padding: 14,
    marginVertical: 5,
    marginHorizontal: 16,
    borderLeftWidth: 3,
    borderLeftColor: '#facc15',
  },
  time: {
    color: '#888',
    fontSize: 12,
    marginBottom: 4,
    fontFamily: 'monospace',
  },
  msg: {
    color: '#facc15',
    fontSize: 14,
    lineHeight: 20,
  },
});
