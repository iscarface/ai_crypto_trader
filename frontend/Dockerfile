FROM node:18

# Set the working directory
WORKDIR /app

# Install dependencies (only once)
COPY package*.json ./
RUN npm install

# Expose port 3000 for the React dev server
EXPOSE 3000
