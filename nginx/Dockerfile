FROM ubuntu:precise
MAINTAINER rgan
RUN apt-get update && apt-get upgrade -y && apt-get install -y curl \
    build-essential \
    zlib1g-dev \
    libpcre3 \
    libpcre3-dev \
    openssl \
    libssl-dev \
    python2.7-dev \
    vim
RUN curl http://nginx.org/download/nginx-1.2.2.tar.gz > nginx-1.2.2.tar.gz \
    && tar -zxvf nginx-1.2.2.tar.gz \
    && cd nginx-1.2.2 \
    && ./configure --sbin-path=/usr/sbin/nginx --conf-path=/etc/nginx/nginx.conf \
    && make && make install
ADD nginx.conf /etc/nginx/nginx.conf
RUN mkdir -p /var/log/nginx && mkdir -p /etc/nginx/{sites-available,sites-enabled}
ADD nginx_site /etc/nginx/sites-available/nginx_site
ADD nginx_site /etc/nginx/sites-enabled/nginx_site
EXPOSE 8080
CMD ["nginx"]