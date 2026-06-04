import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  RefreshControl,
  ActivityIndicator,
  StyleSheet,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import usePolling from '../hooks/usePolling';
import PicoCard from '../components/PicoCard';

const SERVER_IP_KEY = 'serverIp';
const POLL_INTERVAL_KEY = 'pollInterval';
const DEFAULT_IP = '192.168.1.X';

export default function DashboardScreen() {
  const [ipInput, setIpInput] = useState(DEFAULT_IP);
  const [activeUrl, setActiveUrl] = useState(null);
  const [pollInterval, setPollInterval] = useState(5000);

  // Load saved IP and poll interval on mount
  useEffect(() => {
    async function loadSettings() {
      const savedIp = await AsyncStorage.getItem(SERVER_IP_KEY);
      const savedInterval = await AsyncStorage.getItem(POLL_INTERVAL_KEY);
      if (savedIp) setIpInput(savedIp);
      if (savedInterval) setPollInterval(parseInt(savedInterval, 10));
    }
    loadSettings();
  }, []);

  const { data, status, error, loading, refetch } = usePolling(activeUrl, pollInterval);

  const handleConnect = useCallback(async () => {
    const trimmed = ipInput.trim();
    if (!trimmed || trimmed === DEFAULT_IP) return;
    const url = `http://${trimmed}:8080`;
    await AsyncStorage.setItem(SERVER_IP_KEY, trimmed);
    setActiveUrl(url);
  }, [ipInput]);

  const handleStop = useCallback(() => {
    setActiveUrl(null);
  }, []);

  const isConnected = activeUrl !== null && !error;

  const picos = data?.picos ?? [];

  const renderPico = ({ item }) => (
    <PicoCard
      pico={item}
      baseUrl={activeUrl}
      onDoorCommand={refetch}
    />
  );

  const ListHeader = (
    <View>
      {/* Title bar */}
      <View style={styles.headerBar}>
        <Text style={styles.headerTitle}>GreenIOT</Text>
        <View style={[styles.statusDot, isConnected ? styles.dotGreen : styles.dotRed]} />
      </View>

      {/* IP input */}
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={ipInput}
          onChangeText={setIpInput}
          placeholder="Server IP (e.g. 192.168.1.10)"
          placeholderTextColor="#555"
          keyboardType="numeric"
          autoCapitalize="none"
          autoCorrect={false}
        />
      </View>

      {/* Connect / Stop */}
      <View style={styles.btnRow}>
        <TouchableOpacity
          style={[styles.actionBtn, styles.connectBtn]}
          onPress={handleConnect}
          activeOpacity={0.75}
        >
          <Text style={styles.actionBtnText}>Connect</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.actionBtn, styles.stopBtn]}
          onPress={handleStop}
          activeOpacity={0.75}
        >
          <Text style={styles.actionBtnText}>Stop</Text>
        </TouchableOpacity>
      </View>

      {/* Error banner */}
      {error ? (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      {/* Status box */}
      {status ? (
        <View style={styles.statusBox}>
          <Text style={styles.statusLabel}>Server started</Text>
          <Text style={styles.statusValue}>{status.started ?? '—'}</Text>
          <Text style={styles.statusLabel}>Uptime</Text>
          <Text style={styles.statusValue}>{status.uptime ?? '—'}</Text>
        </View>
      ) : null}

      {loading && picos.length === 0 ? (
        <ActivityIndicator color="#4ade80" size="large" style={{ marginTop: 32 }} />
      ) : null}

      {activeUrl && !loading && picos.length === 0 && !error ? (
        <Text style={styles.emptyText}>No Pico data received yet.</Text>
      ) : null}

      {!activeUrl ? (
        <Text style={styles.emptyText}>Enter the server IP and tap Connect.</Text>
      ) : null}
    </View>
  );

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="light-content" backgroundColor="#0f0f1a" />
      <FlatList
        data={picos}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderPico}
        ListHeaderComponent={ListHeader}
        ListFooterComponent={<View style={{ height: 24 }} />}
        refreshControl={
          <RefreshControl
            refreshing={loading}
            onRefresh={refetch}
            tintColor="#4ade80"
            colors={['#4ade80']}
          />
        }
        style={styles.list}
        contentContainerStyle={styles.listContent}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: '#0f0f1a',
  },
  list: {
    flex: 1,
    backgroundColor: '#0f0f1a',
  },
  listContent: {
    paddingBottom: 16,
  },
  headerBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 10,
  },
  headerTitle: {
    color: '#4ade80',
    fontSize: 24,
    fontWeight: '800',
    letterSpacing: 1,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  dotGreen: {
    backgroundColor: '#4ade80',
  },
  dotRed: {
    backgroundColor: '#f87171',
  },
  inputRow: {
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#1e1e2e',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#2a2a3e',
    color: '#fff',
    fontSize: 15,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  btnRow: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    gap: 10,
    marginBottom: 12,
  },
  actionBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: 'center',
  },
  connectBtn: {
    backgroundColor: '#166534',
    borderWidth: 1,
    borderColor: '#4ade80',
  },
  stopBtn: {
    backgroundColor: '#7f1d1d',
    borderWidth: 1,
    borderColor: '#f87171',
  },
  actionBtnText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 14,
  },
  errorBanner: {
    marginHorizontal: 16,
    backgroundColor: '#3b0000',
    borderRadius: 8,
    padding: 10,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#f87171',
  },
  errorText: {
    color: '#f87171',
    fontSize: 13,
    textAlign: 'center',
  },
  statusBox: {
    marginHorizontal: 16,
    backgroundColor: '#1e1e2e',
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#2a2a3e',
  },
  statusLabel: {
    color: '#888',
    fontSize: 12,
    marginBottom: 2,
  },
  statusValue: {
    color: '#4ade80',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    fontFamily: 'monospace',
  },
  emptyText: {
    color: '#555',
    textAlign: 'center',
    marginTop: 32,
    fontSize: 14,
  },
});
