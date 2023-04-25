import asyncio
import logging
from app.dependencies import get_db
from app.workflows.crud import create_and_update_client_kaapana_instance, get_kaapana_instances
from app.workflows.schemas import ClientKaapanaInstanceCreate
from app.database import SessionMaker, engine
from app.config import settings

logging.getLogger().setLevel(logging.INFO)


async def create_kaapana_instance():
    async with SessionMaker() as db:
        try:
            db_kaapana_instances = await get_kaapana_instances(db)
            if not db_kaapana_instances:
                client_kaapana_instance = ClientKaapanaInstanceCreate(**{
                    "ssl_check": True,
                    "automatic_update": False,
                    "automatic_workflow_execution": True,
                    "fernet_encrypted": False,
                    "allowed_dags": [],
                    "allowed_datasets": []
                })
                db_client_kaapana_instance = await create_and_update_client_kaapana_instance(db, client_kaapana_instance=client_kaapana_instance)
            for db_kaapana_instance in db_kaapana_instances:
                if not db_kaapana_instance.remote:
                    if db_kaapana_instance.instance_name != settings.instance_name:
                        client_kaapana_instance = ClientKaapanaInstanceCreate(**db_kaapana_instance.__dict__).dict()
                        await create_and_update_client_kaapana_instance(db, client_kaapana_instance=client_kaapana_instance, action="update")
                        logging.info('Client instance updated!')
                    else:
                        logging.info('Client instance needs no update!')
                    break
        except Exception as e:
            logging.warning('Client instance already created!')
            logging.warning(e)

asyncio.run(create_kaapana_instance())
