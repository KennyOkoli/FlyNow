FROM node:22 AS build
WORKDIR /var/frontend
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.29-alpine
COPY --from=build /var/frontend/dist /usr/share/nginx/html
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
# Where nginx forwards /api. Override per environment (the ECS task definition sets it).
#ENV ENDPOINT=http://backend:8000
EXPOSE 80
