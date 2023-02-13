import os
import logging
import requests
from pathlib import Path
from airflow.exceptions import AirflowFailException
from kaapana.operators.KaapanaPythonBaseOperator import KaapanaPythonBaseOperator
from kaapana.blueprints.kaapana_global_variables import BATCH_NAME, WORKFLOW_DIR


class LocalTrustedPreETLOperator(KaapanaPythonBaseOperator):
    def algo_pre_etl(self, config_params):
        operator_dir = os.path.dirname(os.path.abspath(__file__))
        user_experiment_path = os.path.join(operator_dir, "algorithm_files", config_params["workflow_type"], config_params["experiment_name"])
        Path(user_experiment_path).mkdir(parents=True, exist_ok=True)
        if config_params["workflow_type"] == "shell_workflow":            
            download_url = config_params["download_url"]
            try:
                response = requests.get(download_url)
                response.raise_for_status()
                with open(os.path.join(user_experiment_path, f"{config_params['experiment_name']}.zip"), "wb") as file:
                    file.write(response.content)
            except requests.exceptions.RequestException as e:
                print(f"An error occurred while downloading the file: {e}")
        elif config_params["request_type"] == "container_workflow":
            logging.debug("Downloading container from registry since container workflow is requested...")
            logging.info("Logging into container registry!!!") 
            command = ["skopeo", "login", "--username", f"{config_params['container']['username']}", "--password", f"{config_params['container']['password']}", f"{config_params['container']['registry_url']}"]
            return_code = self.run_command(command=command)
            if return_code == 0:
                logging.info(f"Login to the registry successful!!")
            else:
                raise AirflowFailException("Login to the registry FAILED! Cannot proceed further...")

            logging.debug(f"Pulling container: {config_params['container']['name']}:{config_params['container']['version']}...")
            tarball_file = os.path.join(user_experiment_path, f"{config_params['user_selected_algorithm']}.tar")
            if os.path.exists(tarball_file):
                logging.debug(f"Submission tarball already exists locally... deleting it now to pull latest!!")
                os.remove(tarball_file)
            """Due to absence of /etc/containers/policy.json in Airflow container, following Skopeo command only works with "--insecure-policy" """
            command2 = ["skopeo", "--insecure-policy", "copy", f"docker://{config_params['container']['registry_url']}/{config_params['container']['name']}:{config_params['container']['version']}", f"docker-archive:{tarball_file}", "--additional-tag", f"{config_params['container']['name']}:{config_params['container']['version']}"]
            return_code2 = self.run_command(command=command2)
            if return_code2 != 0:
                raise AirflowFailException(f"Error while trying to download container! Exiting...")        
        else:
            raise AirflowFailException(f"Workflow type {config_params['request_type']} not supported yet! Exiting...")

    
    def start(self, ds, ti, **kwargs):
        logging.info("Prepare data and algorithm before being loaded into the isolated environment...")
        conf = kwargs["dag_run"].conf
        """Prepare algorithm files"""
        self.algo_pre_etl(conf)


    def __init__(self,
                 dag,
                 **kwargs):

        super().__init__(
            dag=dag,
            name="trusted-pre-etl",
            python_callable=self.start,
            **kwargs
        )