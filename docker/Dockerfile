FROM ubuntu:18.04
MAINTAINER Hao Wang "wanghao27@163.com"
ENV PYTHONPATH=/new_test:/new_test/rqalpha DEBIAN_FRONTEND=noninteractive LC_ALL=C.UTF-8 LANG=C.UTF-8
RUN projectDeps='python3 python3-pip git mongodb wget language-pack-zh-hans' \
    && apt-get update \
    && apt-get install -y $projectDeps \
    && locale-gen "en_US.UTF-8" \
    && dpkg-reconfigure --frontend noninteractive locales \
    && echo "Asia/Shanghai" | tee /etc/timezone \
	&& apt-get install -y tzdata \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && wget "http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz" \
    && tar zxvf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib \
    && ./configure --prefix=/usr \
    && make \
    && make install \
    && cd .. \
    && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz
RUN git clone https://github.com/lunasi27/new_test.git
WORKDIR /new_test
RUN cd web \
    && pip3 install -r web/requirements.txt
RUN cd rqalpha \
    && pip3 install -r requirements.txt \
    && rqalpha update-bundle \
    && rqalpha run -f main.py -s 2019-09-01
CMD ["sh", "-c", "service mongodb start; python3 web/manage.py"]
EXPOSE 9000 21017