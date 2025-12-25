# frontend/Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy dependency definitions
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend code
COPY . .

# Start the app (uses the new "start" script which is just React)
CMD ["npm", "start"]