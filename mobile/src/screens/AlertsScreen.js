import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { fetchAlerts } from '../utils/api';
import AlertItem from '../components/AlertItem';

const SERVER_IP_KEY = 'serverIp';

export default function AlertsScreen() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [baseUrl, setBaseUrl] = useState(null);

  useEffect(() => {
    async function loadIp() {
      const ip = await AsyncStorage.getItem(SERVER_IP_KEY);
      if (ip) {
        setBaseUrl(`http://${ip}:8080`);
      }
    }
    loadIp();
  }, []);

  const loadAlerts = useCallback(async () => {
    if (!baseUrl) return;
    setLoading(true);
    setError(null);
    try {
      const result = await fetchAlerts(baseUrl);
      setAlerts(Array.isArray(result) ? result : []);
    } catch (err) {
      setError(err.message || 'Failed to load alerts.');
    } finally {
      setLoading(false);
    }
  }, [baseUrl]);

  useEffect(() => {
    if (baseUrl) loadAlerts();
  }, [baseUrl, loadAlerts]);

  const renderAlert = ({ item }) => <AlertItem alert={item} />;

  const renderEmpty = () => {
    if (loading) return null;
    if (error) {
      return (
        <View style={styles.centerBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      );
    }
    if (!baseUrl) {
      return (
        <View style={styles.centerBox}>
          <Text style={styles.mutedText}>No server configured. Go to Settings.</Text>
        </View>
      );
    }
    return (
      <View style={styles.centerBox}>
        <Text style={styles.okText}>No alerts — all systems normal</Text>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="light-content" backgroundColor="#0f0f1a" />

      {/* Header */}
      <View style={styles.headerBar}>
        <Text style={styles.headerTitle}>Alerts</Text>
        <TouchableOpacity
          style={styles.refreshBtn}
          onPress={loadAlerts}
          disabled={loading || !baseUrl}
          activeOpacity={0.75}
        >
          {loading ? (
            <ActivityIndicator color="#4ade80" size="small" />
          ) : (
            <Text style={styles.refreshText}>Refresh</Text>
          )}
        </TouchableOpacity>
      </View>

      <FlatList
        data={alerts}
        keyExtractor={(item, index) => `${item.time}-${index}`}
        renderItem={renderAlert}
        ListEmptyComponent={renderEmpty}
        ListFooterComponent={<View style={{ height: 24 }} />}
        style={styles.list}
        contentContainerStyle={alerts.length === 0 ? styles.emptyContainer : null}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: '#0f0f1a',
  },
  headerBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1e1e2e',
  },
  headerTitle: {
    color: '#fff',
    fontSize: 22,
    fontWeight: '700',
  },
  refreshBtn: {
    backgroundColor: '#1e1e2e',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderWidth: 1,
    borderColor: '#2a2a3e',
    minWidth: 80,
    alignItems: 'center',
  },
  refreshText: {
    color: '#4ade80',
    fontWeight: '600',
    fontSize: 13,
  },
  list: {
    flex: 1,
  },
  emptyContainer: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  centerBox: {
    alignItems: 'center',
    padding: 32,
  },
  okText: {
    color: '#4ade80',
    fontSize: 16,
    textAlign: 'center',
  },
  mutedText: {
    color: '#555',
    fontSize: 14,
    textAlign: 'center',
  },
  errorText: {
    color: '#f87171',
    fontSize: 14,
    textAlign: 'center',
  },
});
