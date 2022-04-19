FROM python:3.10-slim

ENV FLASK_APP microblog.py
ENV FLASK_ENV production

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY api api
COPY migrations migrations
COPY microblog.py config.py boot.sh ./

EXPOSE 5000
CMD ./boot.sh
