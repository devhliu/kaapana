FROM local-only/base-installer:latest
LABEL IMAGE ="wsiconv"
LABEL VERSION="1.0.0"
LABEL CI_IGNORE="False"

Run mkdir Data
RUN apt-get update
RUN apt install -y default-jre  
RUN apt-get install -y unzip
RUN apt-get install nano
RUN apt-get install -y python3-pip
RUN apt-get install -y libtiff-tools
RUN apt-get install -y bc
RUN apt-get install -y openjdk-8-jdk
RUN apt-get install -y openjdk-8-jre
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
RUN mkdir /idc-wsi-conversion/pixelmed
RUN mkdir /idc-wsi-conversion/jai_imageio
RUN mkdir /idc-wsi-conversion/javax.json-1.0.4
RUN mkdir /idc-wsi-conversion/opencsv-2.4
RUN mkdir Dependencies
RUN unzip pixelmed.jar -d /idc-wsi-conversion/pixelmed/
RUN unzip /idc-wsi-conversion/jai_imageio.jar -d /idc-wsi-conversion/jai_imageio
RUN unzip /idc-wsi-conversion/javax.json-1.0.4.jar -d /idc-wsi-conversion/javax.json-1.0.4
RUN unzip /idc-wsi-conversion/opencsv-2.4.jar -d /idc-wsi-conversion/opencsv-2.4/
RUN tar -xvjf pixelmedjavadicom_dependencyrelease.20221004.tar.bz2 -C /Dependencies/
RUN mv Dependencies/lib/ /idc-wsi-conversion
RUN rm -r Dependencies
RUN rm -r /idc-wsi-conversion/gdcsvstodcm.sh
RUN mkdir idc-wsi-conversion/Data

RUN mv pixelmed.jar /idc-wsi-conversion

COPY files/execute_svs.sh /
COPY files/gdcsvstodcm_svs.sh /
COPY files/execute_tif.sh /
COPY files/gdcsvstodcm_tif.sh /

RUN mv gdcsvstodcm_svs.sh /idc-wsi-conversion
RUN mv gdcsvstodcm_tif.sh /idc-wsi-conversion
RUN chmod +x /idc-wsi-conversion/gdcsvstodcm_svs.sh
RUN chmod +x execute_svs.sh
RUN chmod +x /idc-wsi-conversion/gdcsvstodcm_tif.sh
RUN chmod +x execute_tif.sh



ENTRYPOINT ["/bin/bash","-c","./execute_tif.sh && ./execute_svs.sh"]
CMD ["/bin/bash"]

