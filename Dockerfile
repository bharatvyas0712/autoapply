# Backend Dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY backend/package*.json ./
RUN npm ci --only=production

# Copy backend files
COPY backend/ ./

# Create uploads directory
RUN mkdir -p uploads/screenshots

# Expose port
EXPOSE 3000

# Start server
CMD ["node", "server.js"]
