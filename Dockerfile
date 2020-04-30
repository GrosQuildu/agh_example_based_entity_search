FROM ubuntu:18.04

RUN groupadd -r user && useradd --no-log-init -r -g user user
RUN apt update && apt -y install ca-certificates python3 python3-setuptools

RUN mkdir /home/user && chown user:user -R /home/user 
ADD . /home/user/

USER user
WORKDIR /home/user/
RUN python3 ./setup.py install --user
ENV PATH="${PATH}:/home/user/.local/bin"
ENV PYTHONIOENCODING=UTF-8

CMD ["ebes-rank", "http://dbpedia.org/sparql", "--shell"]