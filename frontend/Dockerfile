FROM node:18-alpine

WORKDIR /app

# Copy dependency mappings
COPY package*.json ./

# Install packages
RUN npm install

# Copy application files
COPY . .

EXPOSE 3000

# Set environment
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# Default to next dev for hot reloading
CMD ["npm", "run", "dev"]
