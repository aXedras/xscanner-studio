# xScanner Studio (Vite) - build static assets and serve via nginx

FROM node:20.19.0-alpine3.21 AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . ./

# Build-time public configuration (baked into the bundle)
ARG VITE_API_URL
ARG VITE_XSCANNER_API_URL
ARG VITE_LOG_LEVEL
ARG VITE_XSCANNER_RELEASE_TAG

ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_XSCANNER_API_URL=${VITE_XSCANNER_API_URL}
ENV VITE_LOG_LEVEL=${VITE_LOG_LEVEL}
ENV VITE_XSCANNER_RELEASE_TAG=${VITE_XSCANNER_RELEASE_TAG}

RUN npm run build


FROM nginx:1.27.5-alpine3.21

RUN apk add --no-cache gettext

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Runtime config injection
COPY env.template.js /usr/share/nginx/html/env.template.js
COPY docker-entrypoint.d/99-env.sh /docker-entrypoint.d/99-env.sh
RUN chmod +x /docker-entrypoint.d/99-env.sh

EXPOSE 80
