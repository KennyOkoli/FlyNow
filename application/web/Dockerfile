FROM node:22 as sub_base
WORKDIR /var/frontend
COPY package*.json .
RUN ci --omit=dev
COPY . .
RUN npm run build

FROM nginx:latest
COPY --from=sub_base /app/dist /usr/share/nginx/html