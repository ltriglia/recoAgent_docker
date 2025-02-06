FROM python:3.9-slim



RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*
ARG GIT_TOKEN
RUN git config --global user.email laura.triglia@sony.com
RUN git clone https://$GIT_TOKEN@github.com/BRL-AI/recoAgent.git
WORKDIR recoAgent/Form
RUN pip install -r requirements.txt

EXPOSE 8502

HEALTHCHECK CMD curl --fail http://localhost:8502/_stcore/health

ENTRYPOINT ["streamlit", "run", "Introduction.py", "--server.port=8502", "--server.address=0.0.0.0"]