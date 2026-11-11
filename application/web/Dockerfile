FROM node:22 AS sub_base
WORKDIR /var/frontend
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:latest
COPY --from=sub_base /var/frontend/dist /usr/share/nginx/html
#COPY nginx.conf /etc/nginx/conf.d/default.conf