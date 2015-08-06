FROM python:3-onbuild

# RUN apt-get install docker && systemctl start docker

RUN pip install --egg .

ENTRYPOINT ["builder"]
