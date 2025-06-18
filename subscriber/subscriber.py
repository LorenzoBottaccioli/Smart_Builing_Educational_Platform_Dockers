#!/usr/bin/env python3
"""
Subscriber MQTT → InfluxDB v1 para simulaciones con batching asíncrono.
Conexión robusta (auto-reconexión, sesión persistente), preserva timestamps de simulación,
y escribe en segundo plano para evitar bloqueos y huecos de datos.
"""
import os
import time
import json
import logging
import threading

import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient
from dotenv import load_dotenv

# 1) Cargar .env
load_dotenv()

# 2) Configuración MQTT
MQTT_BROKER_URL = os.getenv('MQTT_BROKER_URL', 'mosquitto')
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', '1883'))
MQTT_USERNAME   = os.getenv('MQTT_USERNAME') or None
MQTT_PASSWORD   = os.getenv('MQTT_PASSWORD') or None
MQTT_TOPIC      = os.getenv('MQTT_TOPIC', 'simulationRL/#')
MQTT_CLIENT_ID  = os.getenv('MQTT_CLIENT_ID', f"subscriber_RL")

# 3) Configuración InfluxDB v1
INFLUX_HOST   = os.getenv('INFLUX_HOST', 'influxdb')
INFLUX_PORT   = int(os.getenv('INFLUX_PORT', '8086'))
INFLUX_USER   = os.getenv('INFLUX_USERNAME', 'admin')
INFLUX_PASS   = os.getenv('INFLUX_PASSWORD', 'admin123')
INFLUX_DB     = 'controlled_building'

# 4) Parámetros de batching
BATCH_SIZE     = int(os.getenv('BATCH_SIZE', '500'))
BATCH_INTERVAL = float(os.getenv('BATCH_INTERVAL', '2.0'))  # segundos

# 5) Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger('mqtt_influx')

# 6) InfluxDBClient v1
try:
    influx_client = InfluxDBClient(
        host=INFLUX_HOST,
        port=INFLUX_PORT,
        username=INFLUX_USER,
        password=INFLUX_PASS,
        database=INFLUX_DB
    )
    influx_client.create_database(INFLUX_DB)
    logger.info(f"Conectado a InfluxDB v1 en {INFLUX_HOST}:{INFLUX_PORT}, DB={INFLUX_DB}")
except Exception as e:
    logger.error(f"No se pudo conectar a InfluxDB: {e}")
    raise SystemExit(1)

# 7) Buffer y sincronización
data_buffer = []
buffer_lock = threading.Lock()
msg_counter = 0

# 8) Función de flush en segundo plano
def flush_worker():
    while True:
        time.sleep(BATCH_INTERVAL)
        with buffer_lock:
            if not data_buffer:
                continue
            batch = data_buffer.copy()
            data_buffer.clear()
        try:
            influx_client.write_points(batch, time_precision='n')
            logger.info(f"Flushed {len(batch)} points to InfluxDB")
        except Exception as e:
            logger.error(f"Error al flush en InfluxDB: {e}")
            # reinyectar batch
            with buffer_lock:
                data_buffer[0:0] = batch

# Iniciar hilo de flush
threading.Thread(target=flush_worker, daemon=True).start()

# 9) Función para encolar puntos
def enqueue_point(point):
    """Añade punto al buffer y desencadena flush si excede BATCH_SIZE."""
    global msg_counter
    with buffer_lock:
        data_buffer.append(point)
        msg_counter += 1
        count = msg_counter
        buf_len = len(data_buffer)
    # Log periódico cada 1000 mensajes
    if count % 1000 == 0:
        logger.info(f"Enqueued {count} points so far; current buffer size {buf_len}")
    # Flush inmediato si buffer muy grande
    if buf_len >= BATCH_SIZE:
        threading.Thread(target=flush_worker, daemon=True).start()

# 10) Publicar en InfluxDB (simple wrapper)
def publicar_en_influx(topic, payload):
    parts = topic.split('/')
    if len(parts) < 3:
        return
    category, name = parts[1], parts[2]
    meas_map = {'observations': 'simulation_observations', 'actions': 'simulation_actions', 'rewards': 'simulation_rewards'}
    measurement = meas_map.get(category)
    if not measurement:
        return
    # Extraer valor y timestamp
    if isinstance(payload, dict):
        val = payload.get('value')
        ts_val = payload.get('timestamp')
    else:
        val = payload
        ts_val = None
    try:
        val = float(val)
    except Exception:
        return
    # Construir punto
    point = {
        'measurement': measurement,
        'tags': {'name': name},
        'fields': {'value': val}
    }
    if ts_val is not None:
        try:
            point['time'] = int(float(ts_val) * 1e9)
        except Exception:
            point['time'] = int(time.time() * 1e9)
    else:
        point['time'] = int(time.time() * 1e9)
    enqueue_point(point) 

# 11) Callbacks MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Conectado a MQTT broker")
        client.subscribe(MQTT_TOPIC, qos=1)
        logger.info(f"Suscrito a: {MQTT_TOPIC}")
    else:
        logger.error(f"Fallo conexión MQTT, rc={rc}")

def on_disconnect(client, userdata, rc):
    logger.warning(f"Desconectado MQTT (rc={rc}), reconectando...")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
    except Exception:
        return
    publicar_en_influx(msg.topic, payload)

# 12) Main
def main():
    client = mqtt.Client(client_id=MQTT_CLIENT_ID, clean_session=False)
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    while True:
        try:
            client.connect(MQTT_BROKER_URL, MQTT_BROKER_PORT, keepalive=60)
            break
        except Exception:
            time.sleep(5)
    client.loop_forever(retry_first_connection=True)

if __name__ == '__main__':
    main()
