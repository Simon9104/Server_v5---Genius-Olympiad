import React from 'react';
import { View, StyleSheet } from 'react-native';

/**
 * SensorBar — a simple horizontal progress bar.
 *
 * Props:
 *   value  {number}  — current reading
 *   max    {number}  — maximum value (used to compute fill percentage)
 *   color  {string}  — fill colour (e.g. "#60a5fa")
 */
export default function SensorBar({ value = 0, max = 100, color = '#4ade80' }) {
  const clampedValue = Math.max(0, Math.min(value, max));
  const fillPercent = max > 0 ? (clampedValue / max) * 100 : 0;

  return (
    <View style={styles.track}>
      <View
        style={[
          styles.fill,
          { width: `${fillPercent}%`, backgroundColor: color },
        ]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  track: {
    height: 8,
    borderRadius: 4,
    backgroundColor: '#2a2a3e',
    overflow: 'hidden',
    width: '100%',
  },
  fill: {
    height: '100%',
    borderRadius: 4,
  },
});
