# metrics-dashboard — React + D3 dashboard with Node/Express SSE API
FROM node:20-slim
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite dev server (web, :5173) + Express API/SSE (:4000) run together.
EXPOSE 5173 4000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
