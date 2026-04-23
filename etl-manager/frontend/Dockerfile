FROM node:20-slim

WORKDIR /app

# Instala dependências a partir do package-lock/package.json
COPY package*.json ./
RUN npm ci --silent

# Copia o restante do código (será sobrescrito em dev por volume)
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
