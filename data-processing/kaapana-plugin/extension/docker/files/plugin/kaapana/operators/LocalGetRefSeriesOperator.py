import glob
import os
import json
from dataclasses import dataclass
from datetime import timedelta
from multiprocessing.pool import ThreadPool
from os.path import join
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pydicom
import SimpleITK as sitk
from kaapana.operators.HelperCaching import cache_operator_output
from kaapana.operators.HelperDcmWeb import get_dcmweb_helper
from kaapana.operators.KaapanaPythonBaseOperator import KaapanaPythonBaseOperator
from kaapanapy.helper.HelperOpensearch import HelperOpensearch


@dataclass
class DownloadSeries:
    series_instance_uid: str
    reference_series_uid: str
    study_instance_uid: str
    target_dir: str


class LocalGetRefSeriesOperator(KaapanaPythonBaseOperator):
    """
    Operator to get DICOM series.

    This operator downloads DICOM series from a given PACS system according to specified search filters.
    The downloading is executed in a structured manner such that the downloaded data is saved to target directories named with the series_uid.
    """

    def __init__(
        self,
        dag,
        name: str = "get-ref-series",
        search_policy: str = "reference_uid",  # reference_uid, study_uid, patient_uid
        data_type: str = "dicom",
        dicom_tags: list = [],
        parallel_downloads: int = 3,
        batch_name: str = None,
        **kwargs,
    ):
        if data_type not in ["dicom", "json"]:
            raise ValueError("Unknown data-type!")
        if search_policy not in ["reference_uid", "study_uid", "patient_uid"]:
            raise ValueError("Unknown search policy!")

        if search_policy == "patient_uid":
            raise NotImplementedError(
                "search_policy 'patient_uid' is not implemented yet!"
            )

        self.search_policy = search_policy
        self.data_type = data_type
        self.dicom_tags = (
            dicom_tags  # studyID dicom_tags=[{'id':'StudyID','value':'nnUnet'},{...}]
        )

        self.parallel_downloads = parallel_downloads
        self.batch_name = batch_name

        super().__init__(
            dag=dag,
            name=name,
            batch_name=batch_name,
            python_callable=self.get_files,
            execution_timeout=timedelta(minutes=120),
            **kwargs,
        )

    def download_metadata_from_opensearch(self, series: DownloadSeries):
        # Create target directory
        Path(series.target_dir).mkdir(parents=True, exist_ok=True)

        # Get metadata from OpenSearch
        meta_data = HelperOpensearch.get_series_metadata(
            series_instance_uid=series.reference_series_uid
        )

        # Save metadata to json file
        with open(join(series.target_dir, "metadata.json"), "w") as fp:
            json.dump(meta_data, fp, indent=4, sort_keys=True)

    def download_series_from_pacs(self, series: DownloadSeries):
        """Download a series from the PACS system.

        Args:
            series (DownloadSeries): The series to download.
        """

        self.dcmweb_helper.download_series(
            study_uid=series.study_instance_uid,
            series_uid=series.reference_series_uid,
            target_dir=series.target_dir,
        )

    def prepare_download(self, path_to_dicom_slice: str) -> DownloadSeries:
        """Prepare the download of a series. Means:
        - Load the dicom file and get the series instance uid.
        - Get the reference series uid.
        - Get the study instance uid.
        - Depending on the modality, get the reference series uid.
        - Create the target directory for the download.
        - Return a DownloadSeries object, which contains the information needed for the download.

        Args:
            path_to_dicom_slice (str): The path to the dicom slice.

        Raises:
            ValueError: If the modality is unknown.

        Returns:
            DownloadSeries: Dataclass containing the information needed for the download.
        """

        # Load the dicom file
        ds = pydicom.dcmread(join(path_to_dicom_slice))

        # get series instance uid
        series_instance_uid = ds.SeriesInstanceUID
        # get study instance uid
        study_instance_uid = ds.StudyInstanceUID

        if ds.Modality == "SEG":
            # Get the reference series uid
            reference_series_uid = ds.ReferencedSeriesSequence[0].SeriesInstanceUID
        elif ds.Modality == "RTSTRUCT":
            # Get the reference series uid
            reference_series_uid = (
                ds.ReferencedFrameOfReferenceSequence[0]
                .RTReferencedStudySequence[0]
                .RTReferencedSeriesSequence[0]
                .SeriesInstanceUID
            )
        else:
            raise ValueError("Unknown modality!")

        target_dir = join(
            self.airflow_workflow_dir,
            self.dag_run,
            self.batch_name,
            series_instance_uid,
            self.operator_out_dir,
        )

        os.makedirs(target_dir, exist_ok=True)

        return DownloadSeries(
            series_instance_uid=series_instance_uid,
            reference_series_uid=reference_series_uid,
            study_instance_uid=study_instance_uid,
            target_dir=target_dir,
        )

    @cache_operator_output
    def get_files(self, ds, **kwargs):
        self.dag_run = kwargs["dag_run"].run_id
        print("# Starting module LocalGetRefSeriesOperator")
        self.dcmweb_helper = get_dcmweb_helper()

        series_dirs = glob.glob(
            join(
                self.airflow_workflow_dir,
                self.dag_run,
                self.batch_name,
                "*",
            )
        )  # e.g. /kaapana/mounted/workflows/data/service-segmentation-thumbnail-240916111826725386/batch

        download_series_list = []

        if self.search_policy == "reference_uid":
            # Prepare the download
            with ThreadPoolExecutor(max_workers=self.parallel_downloads) as executor:
                futures = [
                    executor.submit(
                        self.prepare_download,
                        join(
                            series_dir,
                            self.operator_in_dir,
                            os.listdir(join(series_dir, self.operator_in_dir))[0],
                        ),
                    )
                    for series_dir in series_dirs
                ]
                for future in as_completed(futures):
                    download_series_list.append(future.result())

        with ThreadPoolExecutor(max_workers=self.parallel_downloads) as executor:
            if self.data_type == "dicom":
                futures = [
                    executor.submit(self.download_series_from_pacs, series)
                    for series in download_series_list
                ]
            elif self.data_type == "json":
                futures = [
                    executor.submit(self.download_metadata_from_opensearch, series)
                    for series in download_series_list
                ]
            for future in as_completed(futures):
                pass
