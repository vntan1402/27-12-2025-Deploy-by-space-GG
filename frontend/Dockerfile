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

# Build arguments for environment variables
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL
ENV DISABLE_ESLINT_PLUGIN=true

# Build the app
RUN yarn build

# Stage 2: Serve with lightweight server
FROM node:18-alpine

WORKDIR /app

# Install serve globally
RUN npm install -g serve

# Copy built files from build stage
COPY --from=build /app/build ./build

# Cloud Run uses PORT environment variable
ENV PORT=8080
EXPOSE 8080

# Start serve on the PORT
CMD ["sh", "-c", "serve -s build -l $PORT"]
