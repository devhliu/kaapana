
import os
import glob
import functools
import shutil
import json
import requests
import tarfile
import gzip

from minio import Minio

from kaapana.blueprints.kaapana_global_variables import BATCH_NAME, WORKFLOW_DIR

##### To be copied

def get_auth_headers(username, password, protocol, host, port, ssl_check, client_id, client_secret):
    payload = {
        'username': username,
        'password': password,
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'password'
    }
    url = f'{protocol}://{host}:{port}/auth/realms/kaapana/protocol/openid-connect/token'
    r = requests.post(url, verify=ssl_check, data=payload)
    access_token = r.json()['access_token']
    return {'Authorization': f'Bearer {access_token}'}

def apply_tar_action(dst_filename, src_dir):
    print(f'Tar {src_dir} to {dst_filename}')
    with tarfile.open(dst_filename, "w:gz") as tar:
        tar.add(src_dir, arcname=os.path.basename(src_dir))

def apply_untar_action(src_filename, dst_dir):
    print(f'Untar {src_filename} to {dst_dir}')
    with tarfile.open(src_filename, "r:gz")as tar:
        tar.extractall(dst_dir)
        
def apply_minio_presigned_url_action(action, federated, operator_out_dir, root_dir):
    data = federated['minio_urls'][operator_out_dir][action]
    print(data)
    minio_presigned_url = f'{federated["host_network"]["protocol"]}://{federated["host_network"]["host"]}:{federated["host_network"]["port"]}/federated-backend/minio-presigned-url'
    ssl_check = federated["host_network"]["ssl_check"]
    filename = os.path.join(root_dir, os.path.basename(data['path'].split('?')[0]))
    if action == 'PUT':
        apply_tar_action(filename, os.path.join(root_dir, operator_out_dir))
        tar = open(filename, "rb")
        print(f'Putting {filename} to {federated["host_network"]}')
        r = requests.post(minio_presigned_url, verify=ssl_check, data=data,  files={'file': tar}, headers=get_auth_headers(**federated["host_network"]))
        r.raise_for_status()

    if action == 'GET':
        print(f'Getting {filename} from {federated["host_network"]}')
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with requests.post(minio_presigned_url, verify=ssl_check, data=data, stream=True, headers=get_auth_headers(**federated["host_network"])) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    # If you have chunk encoded response uncomment if
                    # and set chunk_size parameter to None.
                    #if chunk: 
                    f.write(chunk)
        apply_untar_action(filename, os.path.join(root_dir))
    os.remove(filename)
    
                
def federated_action(operator_out_dir, action, dag_run_dir, federated):


    # if action == 'from_previous_dag_run':
    #     pass
    #     # src = os.path.join(WORKFLOW_DIR, federated['from_previous_dag_run'], operator_out_dir)
    #     # print(src)
    #     # dst = os.path.join(dag_run_dir, operator_out_dir)
    #     # print(dst)
    #     # if os.path.isdir(src):
    #     #     print(f'Moving batch files from {src} to {dst}')
    #     #     shutil.move(src=src, dst=dst)
    if federated['minio_urls'] is not None and operator_out_dir in federated['minio_urls']:
        apply_minio_presigned_url_action(action, federated, operator_out_dir, dag_run_dir)
#         HelperMinio.apply_action_to_object_dirs(minioClient, action, bucket_name=f'{federated["site"]}',
#                                 local_root_dir=dag_run_dir,
#                                 object_dirs=[operator_out_dir])

    # if action == 'from_previous_dag_run':
    #     src_root_dir = os.path.join(WORKFLOW_DIR, federated['from_previous_dag_run'], BATCH_NAME)
    #     dst_root_dir = os.path.join(dag_run_dir, BATCH_NAME)
    #     batch_folders = sorted([f for f in glob.glob(os.path.join(src_root_dir, '*'))])
    #     for batch_element_dir in batch_folders:
    #         src = os.path.join(batch_element_dir, operator_out_dir)
    #         rel_dir = os.path.relpath(src, src_root_dir)
    #         dst = os.path.join(dst_root_dir, rel_dir)
    #         if os.path.isdir(src):
    #             print(f'Moving batch element files from {src} to {dst}')
    #             shutil.move(src=src, dst=dst)
#######################

# Decorator
def federated_sharing_operator(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):

        if 'context' in kwargs:
            run_id = kwargs['context']['run_id']
        elif type(args) == tuple and len(args) == 1 and "run_id" in args[0]:
            run_id = args[0]['run_id']
        else:
            run_id = kwargs['run_id']

        dag_run_dir = os.path.join(WORKFLOW_DIR, run_id)
        
        federated = None
        if 'context' in kwargs:
            print(kwargs)
            print(kwargs['context'])
        else:
            print('caching kwargs', kwargs["dag_run"].conf)
            conf =  kwargs["dag_run"].conf
            if kwargs["dag_run"] is not None and conf is not None and 'federated' in conf and conf['federated'] is not None:
                federated = conf['federated']

        ##### To be copied
        if federated is not None and 'from_previous_dag_run' in federated and federated['from_previous_dag_run'] is not None:
            if 'federated_operators' in federated and self.name in federated['federated_operators']:
                print('Downloading data from Minio')
                federated_action(self.operator_out_dir, 'GET', dag_run_dir, federated)


        x = func(self, *args, **kwargs)
        if federated is not None and 'federated_operators' in federated and self.name in federated['federated_operators']:
            print('Putting data')
            federated_action(self.operator_out_dir, 'PUT', dag_run_dir, federated)

            if federated['federated_operators'].index(self.name) == 0:
                print('Updating the conf')
                conf['federated']['rounds'].append(conf['federated']['rounds'][-1] + 1) 
                conf['federated']['from_previous_dag_run'] = run_id
                os.makedirs(os.path.join(dag_run_dir, 'conf'), exist_ok=True)
                config_path = os.path.join(dag_run_dir, 'conf', 'conf.json')
                with open(config_path, "w", encoding='utf-8') as jsonData:
                    json.dump(conf, jsonData, indent=4, sort_keys=True, ensure_ascii=True)
                federated_action('conf', 'PUT', dag_run_dir, federated)

#                 HelperMinio.apply_action_to_file(minioClient, 'put', 
#                     bucket_name=f'{federated["site"]}', object_name='conf.json', file_path=config_path)
                # Implement removal of file?
#         #######################
        return x

    return wrapper