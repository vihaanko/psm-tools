from ubuntu:20.04

RUN apt update
RUN apt install -y git python3 make python3-distutils curl
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3 get-pip.py
RUN rm get-pip.py
RUN git clone https://github.com/pensando/psm-tools.git
WORKDIR psm-tools/pyclient
RUN pip install -r requirements.txt
ENV DEBIAN_FRONTEND=noninteractive
RUN apt install -y default-jdk
RUN java --version

RUN mkdir $HOME/.psm/
ENV psmip=10.7.100.21
RUN echo {\"psm-ip\": \"$psmip\"} > $HOME/.psm/config.json
RUN make

CMD ["echo", "Hello World!"]