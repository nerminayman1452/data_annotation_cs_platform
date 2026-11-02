FROM nginx:1.25.1-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/nginx.conf
RUN cat /etc/nginx/conf.d/nginx.conf \
    && mkdir -p /opt/application/webapp/staticfiles \
    && ls -al /opt/application/webapp/staticfiles