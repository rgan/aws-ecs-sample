FROM python:2.7
ENV PYTHONUNBUFFERED 1
RUN mkdir -p /var/api && mkdir -p /etc/api
EXPOSE 8000
ADD config.json /etc/api/
ADD requirements.txt .
RUN pip install -r requirements.txt
RUN curl -o code.tar.gz https://github.com/rgan/aws-ecs-example/archive/${APP_VERSION}.tar.gz \
&& tar -xzf code.tar.gz -C /var/api/ \
&& rm code.tar.gz
CMD ["python main.py"]