FROM nginx:1.22.1

# Копируем конфигурационный файл nginx.conf в контейнер
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Копируем файлы документации в контейнер
COPY redoc.html /usr/share/nginx/html/api/docs/redoc.html
COPY openapi-schema.yml /usr/share/nginx/html/api/docs/openapi-schema.yml