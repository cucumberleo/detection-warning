export type Role = 'user' | 'admin'
export type GasType = 'NH3' | 'Toluene' | 'HCHO' | 'TEA'
export type Page = 'dashboard' | 'monitor' | 'alerts' | 'analytics' | 'resources' | 'assistant'

export interface Curve { time: number[]; values: number[]; unit: string }

export interface Detection {
  id: string
  device_id: string
  gas_type: GasType
  concentration_ppm: number
  confidence: number
  response: number
  status: 'safe' | 'warning'
  algorithm_version: string
  processing_latency_ms: number
  created_at: string
  curve: Curve
}

export interface Alert {
  id: string
  detection_id: string
  gas_type: GasType
  device_id: string
  concentration_ppm: number
  status: 'open' | 'acknowledged'
  severity: 'low' | 'medium' | 'high'
  created_at: string
  acknowledged_at: string | null
}

export interface Overview {
  total_detections: number
  warning_count: number
  open_alert_count: number
  online_devices: number
  average_ppm: number
  peak_ppm: number
  gas_counts: Record<string, number>
  trend: Array<{ label: string; value: number }>
}

export interface Device {
  id: string
  name: string
  material: string
  location: string
  status: 'online' | 'offline'
  signal_quality: number
}

export interface PlatformUser {
  id: string
  name: string
  role: Role
  devices: string[]
  status: string
}

export interface AlertRule {
  threshold: number
  severity: 'low' | 'medium' | 'high'
}

export interface Recommendation { module: string; title: string; reason: string; score: number }
export interface SessionUser extends PlatformUser {}
