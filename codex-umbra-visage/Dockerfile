FROM node:20-alpine

WORKDIR /app

# Install dependencies for better caching
COPY package*.json ./
RUN npm ci

# Copy the rest of the application
COPY . .

# Expose Vite's port
EXPOSE 5173

# Run in development mode with host binding
CMD ["npm", "run", "dev"]
