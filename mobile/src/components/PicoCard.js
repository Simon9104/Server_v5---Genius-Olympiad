import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import SensorBar from './SensorBar';
import DoorControls from './DoorControls';

/**
 * PicoCard — shows all sensor data for one Pico.
 *
 * Props:
 *   pico           {{ id, name, humidity, temperature, door, pump, ram }}
 *   baseUrl        {string}    — needed for DoorControls
 *   onDoorCommand  {function}  — called after a door command succeeds
 */
export default function PicoCard({ pico, baseUrl, onDoorCommand }) {
  if (!pico) return null;

  const {
    id,
    name = `Pico ${id}`,
    humidity = 0,
    temperature = 0,
    door = false,
    pump = false,
    ram = 0,
  } = pico;

  // RAM bar colour thresholds
  const ramColor =
    ram >= 80 ? '#f87171' : ram >= 60 ? '#facc15' : '#4ade80';

  return (
    <View style={styles.card}>
      {/* Header */}
      <Text style={styles.title}>{name}</Text>

      {/* Status chips */}
      <View style={styles.chipRow}>
        <View style={[styles.chip, door ? styles.chipGreen : styles.chipGrey]}>
          <Text style={styles.chipText}>{door ? 'DOOR OPEN' : 'DOOR CLOSED'}</Text>
        </View>
        <View style={[styles.chip, pump ? styles.chipGreen : styles.chipGrey]}>
          <Text style={styles.chipText}>{pump ? 'PUMP ON' : 'PUMP OFF'}</Text>
        </View>
      </View>

      {/* Humidity */}
      <View style={styles.sensorRow}>
        <View style={styles.sensorLabelRow}>
          <Text style={styles.sensorLabel}>Humidity</Text>
          <Text style={[styles.sensorValue, { color: '#60a5fa' }]}>
            {humidity.toFixed(1)}%
          </Text>
        </View>
        <SensorBar value={humidity} max={100} color="#60a5fa" />
      </View>

      {/* Temperature */}
      <View style={styles.sensorRow}>
        <View style={styles.sensorLabelRow}>
          <Text style={styles.sensorLabel}>Temperature</Text>
          <Text style={[styles.sensorValue, { color: '#f87171' }]}>
            {temperature.toFixed(1)}°C
          </Text>
        </View>
        <SensorBar value={temperature} max={60} color="#f87171" />
      </View>

      {/* RAM */}
      <View style={styles.sensorRow}>
        <View style={styles.sensorLabelRow}>
          <Text style={styles.sensorLabel}>RAM Usage</Text>
          <Text style={[styles.sensorValue, { color: ramColor }]}>
            {ram.toFixed(0)}%
          </Text>
        </View>
        <SensorBar value={ram} max={100} color={ramColor} />
      </View>

      {/* Door controls */}
      <DoorControls
        picoId={id}
        baseUrl={baseUrl}
        onSuccess={onDoorCommand}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1e1e2e',
    borderRadius: 14,
    padding: 16,
    marginVertical: 8,
    marginHorizontal: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  title: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 12,
  },
  chipRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 14,
  },
  chip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
  },
  chipGreen: {
    backgroundColor: '#14532d',
    borderWidth: 1,
    borderColor: '#4ade80',
  },
  chipGrey: {
    backgroundColor: '#2a2a3e',
    borderWidth: 1,
    borderColor: '#555',
  },
  chipText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  sensorRow: {
    marginBottom: 12,
  },
  sensorLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  sensorLabel: {
    color: '#aaa',
    fontSize: 13,
  },
  sensorValue: {
    fontSize: 13,
    fontWeight: '600',
  },
});
