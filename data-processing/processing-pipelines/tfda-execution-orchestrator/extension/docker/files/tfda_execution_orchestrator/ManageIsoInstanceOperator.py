from kaapana.operators.KaapanaBaseOperator import KaapanaBaseOperator
from kaapana.blueprints.kaapana_global_variables import DEFAULT_REGISTRY, KAAPANA_BUILD_VERSION
from datetime import timedelta

class ManageIsoInstanceOperator(KaapanaBaseOperator):        
    execution_timeout = timedelta(hours=10)
    
    def __init__(self,
                 dag,
                 instanceState = "present",
                 taskName = "create-iso-inst",
                 env_vars={},
                 execution_timeout=execution_timeout,
                 **kwargs):
        name = taskName
        envs = {
            "INSTANCE_STATE": str(instanceState),
            "TASK_TYPE": name
        }
        env_vars.update(envs)

        super().__init__(
            dag=dag,
            image=f"{DEFAULT_REGISTRY}/trigger-ansible-playbook:{KAAPANA_BUILD_VERSION}",
            name=name,
            image_pull_secrets=["registry-secret"],
            execution_timeout=execution_timeout,
            env_vars=env_vars,
            **kwargs
        )

