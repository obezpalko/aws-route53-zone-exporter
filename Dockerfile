FROM python:3.9-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /
ADD templates /templates
ADD static /static
COPY aws_exporter.py /

RUN ln -s /configs /.aws

USER nobody

EXPOSE 8080 8084

CMD ["python", "aws_exporter.py"]
