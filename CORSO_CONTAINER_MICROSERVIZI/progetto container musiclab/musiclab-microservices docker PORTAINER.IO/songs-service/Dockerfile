FROM node:20-slim

WORKDIR /app

# build tools necessari: i binari precompilati di sqlite3 possono
# richiedere una GLIBC più recente di quella dell'immagine base,
# quindi compiliamo il modulo nativo da sorgente (vedi npm install sotto)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 make g++ \
    && rm -rf /var/lib/apt/lists/*

COPY package.json ./
RUN npm install --omit=dev --build-from-source=sqlite3

COPY . .

RUN mkdir -p /app/data
VOLUME ["/app/data"]

EXPOSE 4001

HEALTHCHECK --interval=15s --timeout=5s --retries=5 \
  CMD node -e "fetch('http://localhost:4001/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["node", "server.js"]
