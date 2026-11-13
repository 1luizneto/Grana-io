# Três alvos (specs/011-modo-de-uso/research.md, R-03):
# - dev: servidor do Vite com recarga (compose.yaml);
# - build: gera a versão otimizada em dist/;
# - uso: Nginx sem privilégios servindo dist/ e repassando /api ao backend (compose.uso.yaml).

FROM node:24-alpine AS dev

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]


FROM dev AS build

RUN npm run build


FROM nginxinc/nginx-unprivileged:1.28-alpine AS uso

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080
