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

# Build arguments for environment variables
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL
ENV DISABLE_ESLINT_PLUGIN=true

# Build the app
RUN yarn build

# Stage 2: Serve
FROM node:18-alpine

WORKDIR /app

# Install serve
RUN npm install -g serve

# Copy built files
COPY --from=build /app/build ./build

# Cloud Run PORT
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "serve -s build -l $PORT"]
