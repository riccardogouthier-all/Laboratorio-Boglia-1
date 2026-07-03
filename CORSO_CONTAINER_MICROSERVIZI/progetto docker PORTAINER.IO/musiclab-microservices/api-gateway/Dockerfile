FROM nginx:1.27-alpine

RUN apk add --no-cache wget

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --retries=5 \
  CMD wget -q -O- http://localhost/health || exit 1