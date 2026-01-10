FROM python:3.10.4

WORKDIR /my_web

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python","app.py"]