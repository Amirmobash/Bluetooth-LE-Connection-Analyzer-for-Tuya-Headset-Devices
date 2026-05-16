import re
from collections import defaultdict

def advanced_tuya_connection_analyzer(log_file_path):
    try:
        with open(log_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"❌ Fehler: Datei '{log_file_path}' nicht gefunden.")
        return
    except Exception as e:
        print(f"❌ Fehler beim Lesen der Datei: {e}")
        return

    connection_status = {
        "last_create_time": None,
        "last_disconnect_time": None,
        "is_connected": False,
        "gatt_services_found": False,
        "total_connections": 0,
        "total_disconnections": 0
    }
    devices_found = set()

    patterns = {
        "create_conn": re.compile(r"Sent LE Create Connection(?! Cancel)"),
        "cancel_conn": re.compile(r"Sent LE Create Connection Cancel"),
        "disconnect_cmd": re.compile(r"Sent Disconnect"),
        "disconnect_complete": re.compile(r"Rcvd Disconnect Complete"),
        "conn_complete": re.compile(r"LE Enhanced Connection Complete"),
        "gatt_read": re.compile(r"Read By Group Type Request|Read By Type Request"),
        "tuya_name": re.compile(r"Tuya", re.IGNORECASE)
    }

    print("🔍 Starte tiefgehende Log-Analyse...")
    print("-" * 60)

    for line_num, line in enumerate(lines, 1):
        time_match = re.search(r"^\s*(\d+\.\d+)", line)
        current_time = float(time_match.group(1)) if time_match else None

        if patterns["create_conn"].search(line):
            connection_status["last_create_time"] = current_time
            connection_status["total_connections"] += 1
            print(f"🔌 {current_time:.3f}: Neue Verbindungsanfrage (Versuch Nr. {connection_status['total_connections']})")

        if patterns["conn_complete"].search(line):
            connection_status["is_connected"] = True
            print(f"✅ {current_time:.3f}: Verbindung erfolgreich hergestellt!")

        if patterns["disconnect_cmd"].search(line):
            connection_status["last_disconnect_time"] = current_time
            print(f"⚠️ {current_time:.3f}: Host sendet Disconnect-Befehl.")

        if patterns["disconnect_complete"].search(line):
            connection_status["is_connected"] = False
            connection_status["total_disconnections"] += 1
            print(f"❌ {current_time:.3f}: Verbindung vollständig getrennt (Disconnect Complete).")
            if connection_status["last_create_time"]:
                duration = current_time - connection_status["last_create_time"]
                print(f"   ⏱️ Verbindungsdauer: {duration:.2f} Sekunden")

        if patterns["cancel_conn"].search(line):
            print(f"🚫 {current_time:.3f}: Verbindungsaufbau abgebrochen (Connect Cancel).")

        if patterns["gatt_read"].search(line):
            connection_status["gatt_services_found"] = True
            if not hasattr(advanced_tuya_connection_analyzer, "gatt_printed"):
                print(f"📱 {current_time:.3f}: GATT-Datenaustausch (Geräteprofil) gestartet.")
                advanced_tuya_connection_analyzer.gatt_printed = True

        if patterns["tuya_name"].search(line) and not devices_found:
            name_match = re.search(r'Tuya[\w\s]+', line)
            if name_match:
                devices_found.add(name_match.group())
                print(f"🏷️ Tuya-Gerätename gefunden: {name_match.group()}")

    print("\n" + "="*60)
    print("📋 Abschlussbericht:")
    print(f"   - Anzahl Verbindungsanfragen: {connection_status['total_connections']}")
    print(f"   - Anzahl vollständige Trennungen: {connection_status['total_disconnections']}")
    print(f"   - Verbindung letztendlich hergestellt? {'Ja ✅' if connection_status['is_connected'] else 'Nein ❌'}")
    print(f"   - GATT-Datenaustausch erfolgt? {'Ja' if connection_status['gatt_services_found'] else 'Nein'}")

    if connection_status['total_disconnections'] > 0 and connection_status['total_connections'] > 0:
        if connection_status['gatt_services_found']:
            print("\n💡 Fazit: Verbindung hergestellt, Daten ausgetauscht, dann getrennt.")
            print("   Mögliche Ursache: Gerät (Kopfhörer/Tuya) trennt sich nach Datenempfang (Firmware-Problem)")
            print("   oder Host (Windows) beendet Verbindung wegen fehlender Antwort.")
        else:
            print("\n💡 Fazit: Physische Verbindung hergestellt, aber kein Datenaustausch.")
            print("   Mögliche Ursache: Zielgerät ist im 'geparkten' Zustand (Gekoppelt, aber nicht verbunden).")
            print("   Lösung: Gerät aus Bluetooth-Liste entfernen und erneut koppeln.")
    elif 'total_cancels' in connection_status and connection_status.get('total_cancels', 0) > connection_status['total_connections']:
         print("\n💡 Fazit: Verbindung wurde nie abgeschlossen und ständig abgebrochen.")
         print("   Lösung: Bluetooth-Treiber aktualisieren und sicherstellen, dass Kopfhörer im Pairing-/Erkennungsmodus ist.")

if __name__ == "__main__":
    log_file_path = r"C:\path\to\your\wireshark_log.txt"
    advanced_tuya_connection_analyzer(log_file_path)