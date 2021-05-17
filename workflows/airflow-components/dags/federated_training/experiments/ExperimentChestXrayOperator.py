import os
import glob
from datetime import timedelta

from kaapana.blueprints.kaapana_global_variables import BATCH_NAME, WORKFLOW_DIR

# from kaapana.operators.KaapanaBaseOperator import KaapanaBaseOperator, default_registry, default_project
# --> TODO: on_success_back back owerwrite must be possible


class ExperimentChestXrayOperator(KaapanaBaseOperator):

    @staticmethod
    def on_success(info_dict):
        print("##################################################### on_success!")
        pod_id = info_dict["ti"].task.kube_name
        print("--> task completed - now delete pod {} !".format(pod_id))
        KaapanaBaseOperator.pod_stopper.stop_pod_by_name(pod_id=pod_id)
    
    
    def __init__(self,
                 dag,
                 name=None,
                 init_model=False,
                 inference=None,
                 procedure=None,
                 fed_round=None,
                 fed_rounds_total=None,
                 participants=None,
                 worker=None,
                 learning_rate=None,
                 env_vars=None,
                 execution_timeout=timedelta(hours=1),
                 *args, **kwargs
                 ):

        if env_vars is None:
            env_vars = {}
        
        envs = {
            "INIT_MODEL": str(init_model),
            "INFERENCE": str(inference),
            "PROCEDURE": str(procedure),
            "FED_ROUND": str(fed_round),
            "FED_ROUNDS_TOTAL": str(fed_rounds_total),
            "PARTICIPANTS": str(participants),
            "WORKER": str(worker),
            "LEARNING_RATE": str(learning_rate)
        }

        env_vars.update(envs)

        self.name = "fed-exp-chest-xray" if name is None else name

        super().__init__(
            dag=dag,
            name=self.name,
            image="{}{}/federated-exp-chest-xray:0.1.0-vdev".format(default_registry, default_project),
            image_pull_secrets=["registry-secret"],
            env_vars=env_vars,
            on_success_callback=ExperimentChestXrayOperator.on_success,
            execution_timeout=execution_timeout,
            training_operator=True,
            image_pull_policy='Always',
            *args, **kwargs
            )
