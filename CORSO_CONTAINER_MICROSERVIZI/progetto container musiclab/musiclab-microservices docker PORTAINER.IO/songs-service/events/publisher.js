import amqp from 'amqplib';

const RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://guest:guest@rabbitmq:5672';
const EXCHANGE      = 'songs.events';   // exchange di tipo "topic"

let channel = null;

/**
 * Si connette a RabbitMQ con retry (utile perché in docker-compose i
 * container non partono in ordine garantito: il broker potrebbe non
 * essere ancora pronto quando parte questo servizio).
 */
export async function connectPublisher(retries = 15, delayMs = 3000) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const connection = await amqp.connect(RABBITMQ_URL);
      channel = await connection.createChannel();
      await channel.assertExchange(EXCHANGE, 'topic', { durable: true });

      connection.on('close', () => {
        console.warn('[rabbitmq] connessione chiusa, riprovo tra qualche secondo...');
        channel = null;
        setTimeout(() => connectPublisher(), delayMs);
      });

      console.log('[rabbitmq] publisher connesso, exchange pronto:', EXCHANGE);
      return;
    } catch (err) {
      console.warn(`[rabbitmq] tentativo ${attempt}/${retries} fallito: ${err.message}`);
      await new Promise(r => setTimeout(r, delayMs));
    }
  }
  console.error('[rabbitmq] impossibile connettersi al broker, il publisher resterà disattivo');
}

/**
 * Pubblica un evento di dominio.
 * routingKey esempi: "song.created" | "song.updated" | "song.deleted"
 */
export function publishEvent(routingKey, payload) {
  if (!channel) {
    console.warn(`[rabbitmq] canale non disponibile, evento "${routingKey}" scartato`);
    return;
  }
  const buffer = Buffer.from(JSON.stringify(payload));
  channel.publish(EXCHANGE, routingKey, buffer, {
    contentType: 'application/json',
    persistent: true,
  });
  console.log(`[rabbitmq] evento pubblicato: ${routingKey}`, payload);
}
