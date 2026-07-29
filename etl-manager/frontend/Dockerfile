FROM node:20-slim

WORKDIR /app

# Instala dependências a partir do package-lock/package.json
COPY package*.json ./
RUN npm ci --silent

# Copia o restante do código (será sobrescrito em dev por volume)
COPY . .

# Imagem node:20-slim ja traz o usuario "node" (nao-root) pronto - so
# garantir que ele tenha acesso de escrita ao /app (bind mount do host em
# dev + volume nomeado de node_modules) antes de trocar de usuario.
RUN chown -R node:node /app
USER node

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
