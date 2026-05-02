#!/usr/bin/env bash

set -euo pipefail

PRIMARY_SSID="iqoo"
PRIMARY_PASSWORD="12345678"
SECONDARY_SSID=$'\u65af\u662f\u964b\u5ba4 \u60df\u543e\u5fb7\u99a8'
SECONDARY_PASSWORD="fxbfbxjyczbw327"

PRIMARY_CONN_NAME="wifi-iqoo"
SECONDARY_CONN_NAME="wifi-backup"

log() {
  printf '[wifi-connect] %s\n' "$1"
}

require_nmcli() {
  if ! command -v nmcli >/dev/null 2>&1; then
    log "nmcli not found. Please install and enable NetworkManager."
    exit 1
  fi
}

get_wifi_device() {
  nmcli -t -f DEVICE,TYPE,STATE device status | awk -F: '$2=="wifi"{print $1; exit}'
}

ensure_wifi_radio_on() {
  nmcli radio wifi on >/dev/null
}

wait_for_networkmanager() {
  local retries=15
  local count=0

  until nmcli general status >/dev/null 2>&1; do
    count=$((count + 1))
    if [ "$count" -ge "$retries" ]; then
      log "NetworkManager is not ready."
      exit 1
    fi
    sleep 2
  done
}

ensure_connection_profile() {
  local conn_name="$1"
  local ssid="$2"
  local password="$3"
  local priority="$4"

  if nmcli -t -f NAME connection show | grep -Fx "$conn_name" >/dev/null 2>&1; then
    nmcli connection modify "$conn_name" \
      connection.id "$conn_name" \
      connection.autoconnect yes \
      connection.autoconnect-priority "$priority" \
      802-11-wireless.ssid "$ssid" \
      802-11-wireless-security.key-mgmt wpa-psk \
      802-11-wireless-security.psk "$password" \
      ipv4.method auto \
      ipv6.method auto >/dev/null
  else
    nmcli connection add type wifi con-name "$conn_name" ifname "*" ssid "$ssid" \
      802-11-wireless-security.key-mgmt wpa-psk \
      802-11-wireless-security.psk "$password" \
      ipv4.method auto \
      ipv6.method auto \
      connection.autoconnect yes \
      connection.autoconnect-priority "$priority" >/dev/null
  fi
}

scan_wifi_list() {
  local device="$1"
  nmcli device wifi rescan ifname "$device" >/dev/null 2>&1 || true
  sleep 3
  nmcli -t -f SSID device wifi list ifname "$device" | sed '/^$/d'
}

ssid_exists() {
  local target_ssid="$1"
  shift
  printf '%s\n' "$@" | grep -Fx "$target_ssid" >/dev/null 2>&1
}

connect_profile() {
  local conn_name="$1"
  local device="$2"

  log "Trying connection: $conn_name"
  nmcli connection up "$conn_name" ifname "$device"
}

main() {
  require_nmcli
  wait_for_networkmanager
  ensure_wifi_radio_on

  local wifi_device
  wifi_device="$(get_wifi_device)"
  if [ -z "$wifi_device" ]; then
    log "No WiFi device found."
    exit 1
  fi

  log "Using WiFi device: $wifi_device"

  ensure_connection_profile "$PRIMARY_CONN_NAME" "$PRIMARY_SSID" "$PRIMARY_PASSWORD" 100
  ensure_connection_profile "$SECONDARY_CONN_NAME" "$SECONDARY_SSID" "$SECONDARY_PASSWORD" 50

  mapfile -t ssid_list < <(scan_wifi_list "$wifi_device")

  if ssid_exists "$PRIMARY_SSID" "${ssid_list[@]:-}"; then
    log "Preferred SSID found: $PRIMARY_SSID"
    connect_profile "$PRIMARY_CONN_NAME" "$wifi_device"
    exit 0
  fi

  if ssid_exists "$SECONDARY_SSID" "${ssid_list[@]:-}"; then
    log "Fallback SSID found: $SECONDARY_SSID"
    connect_profile "$SECONDARY_CONN_NAME" "$wifi_device"
    exit 0
  fi

  log "Preferred SSIDs not found. Falling back to autoconnect priority."
  nmcli connection up "$PRIMARY_CONN_NAME" ifname "$wifi_device" >/dev/null 2>&1 || true
  nmcli connection up "$SECONDARY_CONN_NAME" ifname "$wifi_device" >/dev/null 2>&1 || true
  exit 0
}

main "$@"
