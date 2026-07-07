FROM node:20-slim

WORKDIR /app

# build tools necessari: i binari precompilati di sqlite3 possono
# richiedere una GLIBC più recente di quella dell'immagine base,
# quindi compiliamo il modulo nativo da sorgente (vedi npm install sotto).
# ffmpeg: genera i file audio demo (placeholder) in fase di build.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 make g++ ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY package.json ./
RUN npm install --omit=dev --build-from-source=sqlite3

COPY . .

# Genera 12 brevi toni audio di esempio (NON brani reali: usati solo per
# dimostrare schema DB + storage + streaming + player, evitando qualunque
# problema di licenza legato a includere audio protetto da copyright nel
# repository/immagine). Il numero deve combaciare con NUM_CAMPIONI_AUDIO
# in routes/canzoniRouter.js.
RUN mkdir -p public/audio && \
    i=1; \
    while [ "$i" -le 12 ]; do \
      freq=$((200 + i * 35)); \
      idx=$(printf "%02d" "$i"); \
      ffmpeg -hide_banner -loglevel error -f lavfi -i "sine=frequency=${freq}:duration=8" \
             -ac 2 -ar 44100 -b:a 128k -y "public/audio/sample-${idx}.mp3"; \
      i=$((i + 1)); \
    done

RUN mkdir -p /app/data
VOLUME ["/app/data"]

EXPOSE 4001

HEALTHCHECK --interval=15s --timeout=5s --retries=5 \
  CMD node -e "fetch('http://localhost:4001/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["node", "server.js"]
