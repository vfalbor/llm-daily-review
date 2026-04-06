FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --production
COPY src/ ./src/
COPY skills/ ./skills/
RUN mkdir -p /app/data/reports
EXPOSE 3000
CMD ["node", "src/web/server.js"]
