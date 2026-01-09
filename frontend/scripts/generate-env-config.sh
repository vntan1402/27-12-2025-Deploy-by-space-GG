#!/bin/bash

# Generate env-config.js from environment variables at container startup
# This allows runtime configuration of React apps

ENV_CONFIG_PATH="/app/build/env-config.js"

# Create the env-config.js file with actual environment variables
cat > $ENV_CONFIG_PATH << EOF
// Generated at container startup - DO NOT EDIT
window._env_ = {
  REACT_APP_BACKEND_URL: "${REACT_APP_BACKEND_URL:-http://localhost:8001}",
  REACT_APP_VERSION: "${REACT_APP_VERSION:-2.0.0}"
};
EOF

echo "✅ Generated env-config.js with REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}"
