FROM mcr.microsoft.com/playwright:focal

WORKDIR /work

# Copy frontend project into container
COPY frontend/ ./frontend/

WORKDIR /work/frontend

# Install node modules and build the frontend
RUN npm ci --silent
RUN npm run build --silent || true

# Ensure Playwright browsers are installed (image already contains browsers)
RUN npx playwright install --with-deps || true

# Default command: run Playwright tests
CMD ["npx", "playwright", "test", "--reporter=dot"]
