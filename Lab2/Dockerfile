FROM tensorflow/tensorflow:latest

ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/pawdentity

WORKDIR $APP_HOME

COPY requirements.txt $APP_HOME/requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends \
    libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip \
    && pip install --no-cache-dir --ignore-installed -r requirements.txt

COPY . /$APP_HOME
EXPOSE 5000

CMD ["python", "backend.py"]
