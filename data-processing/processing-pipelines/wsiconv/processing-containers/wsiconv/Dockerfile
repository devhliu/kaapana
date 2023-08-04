FROM local-only/base-python-cpu:latest
LABEL IMAGE="wsiconv"
LABEL VERSION="1.0.0"
LABEL CI_IGNORE="False"

WORKDIR /kaapana/app
Run mkdir Data
RUN apt-get update
#RUN apt-get update -y && apt-get install -y --no-install-recommends alien && rm -rf /var/lib/apt/lists/*
#RUN wget https://github.com/ibmruntimes/semeru8-binaries/releases/download/jdk8u372-b07_openj9-0.38.0/ibm-semeru-open-8-jdk-1.8.0.372.b07_0.38.0-1.x86_64.rpm -P /tmp/ && alien -i /tmp/*.rpm
#RUN ln -s /usr/lib/jvm/ibm-semeru-open-8-jdk/bin/java /bin
#ENV JAVA_HOME=/usr/lib/jvm/ibm-semeru-open-8-jdk
RUN apt-get install -y unzip
RUN apt-get install nano
RUN apt-get install -y python3-pip
RUN apt-get install -y libtiff-tools
RUN apt-get install -y bc


RUN apt-get install -y dicom3tools
RUN pip install tifffile
RUN pip install pydicom
RUN apt-get -y install git
RUN git clone https://github.com/ImagingDataCommons/idc-wsi-conversion.git
RUN apt install wget
RUN wget http://www.dclunie.com/pixelmed/software/20221004_current/pixelmed.jar
RUN wget http://www.dclunie.com/pixelmed/software/20221004_current/pixelmedjavadicom_dependencyrelease.20221004.tar.bz2

#RUN wget https://github.com/maxfscher/DICOMwsiWorkflow/raw/main/execute.sh
#RUN wget https://github.com/maxfscher/DICOMwsiWorkflow/raw/main/gdcsvstodcm.sh
RUN mkdir -p /idc-wsi-conversion/pixelmed
RUN mkdir -p /idc-wsi-conversion/jai_imageio
RUN mkdir -p /idc-wsi-conversion/javax.json-1.0.4
RUN mkdir -p /idc-wsi-conversion/opencsv-2.4
RUN mkdir -p /Dependencies
RUN unzip -p pixelmed.jar -d /idc-wsi-conversion/pixelmed/
RUN unzip -p idc-wsi-conversion/jai_imageio.jar -d /idc-wsi-conversion/jai_imageio
RUN unzip -p idc-wsi-conversion/javax.json-1.0.4.jar -d /idc-wsi-conversion/javax.json-1.0.4
RUN unzip -p idc-wsi-conversion/opencsv-2.4.jar -d /idc-wsi-conversion/opencsv-2.4/
RUN tar -xvjf pixelmedjavadicom_dependencyrelease.20221004.tar.bz2 -C /Dependencies/
RUN mv /Dependencies/lib/ /idc-wsi-conversion
RUN rm -r /Dependencies
RUN rm -r idc-wsi-conversion/gdcsvstodcm.sh
RUN mkdir idc-wsi-conversion/Data


RUN mv pixelmed.jar /idc-wsi-conversion

COPY files/execute_svs.sh /kaapana/app
COPY files/gdcsvstodcm_svs.sh /kaapana/app
COPY files/execute_tif.sh /kaapana/app
COPY files/gdcsvstodcm_tif.sh /kaapana/app

RUN mv gdcsvstodcm_svs.sh /idc-wsi-conversion
RUN mv gdcsvstodcm_tif.sh /idc-wsi-conversion
RUN chmod +x /idc-wsi-conversion/gdcsvstodcm_svs.sh
RUN chmod +x execute_svs.sh
RUN chmod +x /idc-wsi-conversion/gdcsvstodcm_tif.sh
RUN chmod +x execute_tif.sh


ENTRYPOINT ["/bin/bash","-c","./kaapana/app/execute_tif.sh && ./kaapana/app/execute_svs.sh"]
CMD ["/bin/bash"]

