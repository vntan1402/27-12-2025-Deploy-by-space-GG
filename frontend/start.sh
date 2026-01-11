#!/bin/sh

# Generate env-config.js from environment variables at container startup
# This allows runtime configuration of React apps on Cloud Run

ENV_CONFIG_PATH="./build/env-config.js"

# Get values from environment variables or use defaults
BACKEND_URL="${REACT_APP_BACKEND_URL:-http://localhost:8001}"
APP_VERSION="${REACT_APP_VERSION:-2.0.0}"

echo "Generating env-config.js..."
echo "REACT_APP_BACKEND_URL: $BACKEND_URL"
echo "REACT_APP_VERSION: $APP_VERSION"

# Create the env-config.js file with actual environment variables
cat > $ENV_CONFIG_PATH << EOF
window._env_ = {
  REACT_APP_BACKEND_URL: "$BACKEND_URL",
  REACT_APP_VERSION: "$APP_VERSION"
};
EOF

echo "env-config.js generated successfully!"

# Start the server
echo "Starting server on port $PORT..."
exec serve -s build -l $PORT
