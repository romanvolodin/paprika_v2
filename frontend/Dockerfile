FROM node:22-alpine AS base
WORKDIR /app
COPY package.json package-lock.json .npmrc ./

FROM base AS dev
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]
