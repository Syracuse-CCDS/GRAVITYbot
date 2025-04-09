FROM python:3.10

RUN python -m pip install \
    requests \
    dotenv \
    pandas \
    openai \
    panoptes-client \
    feedparser \
    beautifulsoup4 \
    lxml \
    Markdown \
    markdownify

#VOLUME /var/task/
#COPY . /var/task/
WORKDIR /var/task/
