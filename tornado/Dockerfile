FROM python:2.7
ENV PYTHONUNBUFFERED 1
RUN mkdir -p /var/api && mkdir -p /etc/api
EXPOSE 8000
ADD config.json /etc/api/
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD api.tar.gz /var/api/
CMD ["python", "/var/api/main.py"]