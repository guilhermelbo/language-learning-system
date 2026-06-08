FROM node:22-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Set environment variable
ENV NEXT_PUBLIC_API_URL=http://localhost:8000

# Build and run
EXPOSE 3000
CMD ["npm", "run", "dev"]
