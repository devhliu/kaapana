FROM local-only/base-python-cpu:latest

# ENV http_proxy http://www-int2.dkfz-heidelberg.de:80
# ENV https_proxy http://www-int2.dkfz-heidelberg.de:80

LABEL IMAGE="airflow"
LABEL VERSION="2.2.5"
LABEL CI_IGNORE="False"

ENV SLUGIFY_USES_TEXT_UNIDECODE=yes

ENV DCMDICTPATH /scripts/dicom.dic
ENV DICT_PATH /scripts/dicom_tag_dict.json

WORKDIR /kaapana/app

# run update again
RUN apt-get update -q -y &&  apt-get dist-upgrade -q -y
RUN apt-get update -q -y && apt-get install -y --no-install-recommends \
        wget \
        curl \
        nano \
        unzip \
        zip \
        openssh-client \
        vim \
        skopeo \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip && python3 -m pip install -U setuptools

COPY files/requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements.txt --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.5.1/constraints-3.9.txt"

COPY files/scripts/ /scripts

RUN ansible-galaxy collection install openstack.cloud:==1.8.0
RUN ansible-galaxy collection install community.docker
COPY files/bootstrap.sh /kaapana/app/bootstrap.sh
RUN chmod +x /kaapana/app/bootstrap.sh

COPY files/scheduler_job.py /usr/local/lib/python3.9/site-packages/airflow/jobs/

RUN mkdir -p /root/.ssh
ENTRYPOINT ["/kaapana/app/bootstrap.sh"]
