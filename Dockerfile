FROM getcarrier/performance:base-latest


WORKDIR /opt
ENV compile false
ENV lg_name perfgun
ENV lg_id 1
ARG UNAME=carrier
ARG UID=1001
ARG GID=1001

RUN mkdir -p gatling

# Install utilities
RUN add-apt-repository ppa:deadsnakes/ppa && apt-get update && \
    apt-get install -y --no-install-recommends bash git gfortran python3.7 python3.7-dev python3.7-distutils python3-apt && \
    wget https://bootstrap.pypa.io/get-pip.py && python3.7 get-pip.py && \
    ln -s /usr/bin/python3.7 /usr/local/bin/python3 && \
    ln -s /usr/bin/python3.7 /usr/local/bin/python && \
    python -m pip install --upgrade pip && \
    apt-get clean && \
    python -m pip install setuptools==40.6.2 && \
    python -m pip install 'common==0.1.2' 'configobj==5.0.6' 'redis==3.2.0' 'argparse==1.4.0' && \
    rm -rf /tmp/*

RUN pip install git+https://github.com/carrier-io/perfreporter.git
RUN pip install git+https://github.com/carrier-io/loki_logger.git

# Creating carrier user and making him sudoer
RUN groupadd -g $GID $UNAME
RUN useradd -m -u $UID -g $GID -s /bin/bash $UNAME
RUN echo "carrier    ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Installing Java Jolokia
RUN  mkdir /opt/java && cd /opt/java \
 && wget -O jolokia-jvm-1.6.0-agent.jar \
 http://search.maven.org/remotecontent?filepath=org/jolokia/jolokia-jvm/1.6.0/jolokia-jvm-1.6.0-agent.jar

# Installing Telegraf
RUN cd /tmp && wget https://dl.influxdata.com/telegraf/releases/telegraf_1.10.4-1_amd64.deb && \
    dpkg -i telegraf_1.10.4-1_amd64.deb

COPY telegraf.conf /etc/telegraf/telegraf.conf
COPY telegraf_test_results.conf /etc/telegraf/telegraf_test_results.conf
COPY telegraf_local_results.conf /etc/telegraf/telegraf_local_results.conf
COPY jolokia.conf /opt

ENV PATH /opt/gatling/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH

RUN chown -R ${UNAME}:${UNAME} /opt/gatling
RUN chown -R ${UNAME}:${UNAME} /opt/gatling/


RUN apt-get update && \
  DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -qy \
  tzdata ca-certificates libsystemd-dev && \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN wget https://mirrors.estointernet.in/apache/maven/maven-3/3.6.3/binaries/apache-maven-3.6.3-bin.tar.gz
RUN tar -xvf apache-maven-3.6.3-bin.tar.gz

ENV M2_HOME='/opt/apache-maven-3.6.3'
ENV PATH="$M2_HOME/bin:$PATH"

RUN mvn -version

USER ${UNAME}

RUN mkdir -p /opt/gatling/bin
RUN mkdir -p /opt/gatling/conf
RUN mkdir -p /opt/gatling/lib
RUN mkdir -p /opt/gatling/src
COPY executor.sh /opt
RUN sudo chmod +x /opt/executor.sh
COPY post_processing/post_processor.py /opt/gatling/bin
COPY post_processing/downsampling.py /opt/gatling/bin
COPY pre_processing/minio_reader.py /opt/gatling/bin
COPY pre_processing/minio_poster.py /opt/gatling/bin
COPY pre_processing/minio_args_poster.py /opt/gatling/bin
COPY pre_processing/minio_additional_files_reader.py /opt/gatling/bin
COPY pom.xml /opt/gatling
COPY src/ /opt/gatling/src
COPY libs/gatling-core-3.7.6.jar /opt/gatling/lib
COPY libs/gatling-http-3.7.6.jar /opt/gatling/lib
RUN mvn gatling:test -f pom.xml -Dgatling.simulationClass=computerdatabase.FloodIoJava -Dlogback.configurationFile=logback.xml
COPY libs/gatling-core-3.7.6.jar /home/carrier/.m2/repository/io/gatling/gatling-core/3.7.6
COPY libs/gatling-http-3.7.6.jar /home/carrier/.m2/repository/io/gatling/gatling-http/3.7.6

COPY logback.xml /opt/gatling/conf

ENTRYPOINT ["/opt/executor.sh"]