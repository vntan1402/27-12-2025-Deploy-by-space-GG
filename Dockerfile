# Frontend Dockerfile for Google Cloud Run
# Stage 1: Build
FROM node:20-alpine as build

WORKDIR /app

# Copy package files from frontend folder
COPY frontend/package.json frontend/yarn.lock ./

# Install dependencies (without frozen-lockfile for compatibility)
RUN yarn install

# Copy source code from frontend folder
COPY frontend/ .

# Disable ESLint for build
ENV DISABLE_ESLINT_PLUGIN=true

# Build the app (env-config.js will be generated at runtime)
RUN yarn build

# Stage 2: Serve
FROM node:20-alpine

WORKDIR /app

# Install serve
RUN npm install -g serve

# Copy built files
COPY --from=build /app/build ./build

# Copy startup script
COPY frontend/start.sh ./start.sh
RUN chmod +x ./start.sh

# Cloud Run PORT
ENV PORT=8080
EXPOSE 8080

# Use startup script to generate env-config.js from environment variables
CMD ["./start.sh"]
