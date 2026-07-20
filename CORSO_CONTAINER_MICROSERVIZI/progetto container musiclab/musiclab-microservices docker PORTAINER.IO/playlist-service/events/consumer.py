import json
import os
import threading
import time

import pika

from db import get_connection

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672")
EXCHANGE = "songs.events"
QUEUE_NAME = "playlist_songs_sync"


def _handle_message(routing_key: str, payload: dict):
    conn = get_connection()
    try:
        if routing_key in ("song.created", "song.updated"):
            conn.execute(
                """
                INSERT INTO canzoni_cache (id, titolo, artista, album)
                VALUES (:id, :titolo, :artista, :album)
                ON CONFLICT(id) DO UPDATE SET
                    titolo = excluded.titolo,
                    artista = excluded.artista,
                    album = excluded.album
                """,
                payload,
            )
        elif routing_key == "song.deleted":
            song_id = payload["id"]
            # rimuove la canzone dalla cache locale...
            conn.execute("DELETE FROM canzoni_cache WHERE id = ?", (song_id,))
            # ...e da ogni playlist in cui compariva (prima gestito da
            # ON DELETE CASCADE nel monolite, ora responsabilità di
            # questo servizio, notificato in modo asincrono via broker).
            conn.execute("DELETE FROM playlist_canzoni WHERE canzone_id = ?", (song_id,))
        conn.commit()
        print(f"[rabbitmq] evento consumato: {routing_key} -> {payload}")
    finally:
        conn.close()


def _on_message(channel, method, properties, body):
    try:
        payload = json.loads(body)
        _handle_message(method.routing_key, payload)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:  # noqa: BLE001
        print(f"[rabbitmq] errore elaborazione messaggio: {exc}")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def _consume_loop():
    while True:
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.queue_bind(queue=QUEUE_NAME, exchange=EXCHANGE, routing_key="song.*")
            channel.basic_qos(prefetch_count=10)
            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=_on_message)
            print("[rabbitmq] consumer avviato, in ascolto su", QUEUE_NAME)
            channel.start_consuming()
        except Exception as exc:  # noqa: BLE001
            print(f"[rabbitmq] consumer disconnesso ({exc}), retry tra 5s...")
            time.sleep(5)


def start_consumer_thread():
    thread = threading.Thread(target=_consume_loop, daemon=True)
    thread.start()
