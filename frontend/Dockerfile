# Frontend Dockerfile for Google Cloud Run
# Stage 1: Build
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package.json yarn.lock ./

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy source code
COPY . .

# Disable ESLint for build
ENV DISABLE_ESLINT_PLUGIN=true

# Build the app (env-config.js will be generated at runtime)
RUN yarn build

# Stage 2: Serve with lightweight server
FROM node:18-alpine

WORKDIR /app

# Install serve globally
RUN npm install -g serve

# Copy built files from build stage
COPY --from=build /app/build ./build

# Copy startup script and make executable
COPY start.sh ./start.sh
RUN chmod +x ./start.sh

# Cloud Run uses PORT environment variable
ENV PORT=8080
EXPOSE 8080

# Use startup script to generate env-config.js from environment variables
CMD ["/bin/sh", "./start.sh"]
