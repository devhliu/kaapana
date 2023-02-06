from fastapi import APIRouter, Response, HTTPException, Depends
from datetime import datetime
from app.dependencies import get_minio
from app.config import settings
import json
import os
import socket
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from sqlalchemy.orm import Session
from app.dependencies import get_db

router = APIRouter(tags=["storage"])

def requests_retry_session(
    retries=16,
    backoff_factor=1,
    status_forcelist=[404, 429, 500, 502, 503, 504],
    session=None,
    use_proxies=False
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    if use_proxies is True:
        proxies = {
            'http': os.getenv('PROXY', None),
            'https': os.getenv('PROXY', None),
            'no_proxy': 'airflow-service.flow,airflow-service.flow.svc,' \
                'ctp-dicom-service.flow,ctp-dicom-service.flow.svc,'\
                    'dcm4chee-service.store,dcm4chee-service.store.svc,'\
                        'opensearch-service.meta,opensearch-service.meta.svc'\
                            'kaapana-backend-service.base,kaapana-backend-service.base.svc,' \
                                'minio-service.store,minio-service.store.svc'
        }
        session.proxies.update(proxies)
    
    return session


@router.get('/datasets')
def listbuckets(db: Session = Depends(get_db)):
    """Return List of Minio buckets
    """
    '''buckets = minio.list_buckets()
    data = []
    for bucket in buckets:
        data.append({
          'name':str(bucket.name),
          'creation_date': bucket.creation_date,
          'webui':f'https://{settings.hostname}/minio/{bucket.name}'
        })
    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    #print(requests.get_cohort_names)'''


    #return data

    #data =  requests.get("https://vm-129-196.cloud.dkfz-heidelberg.de/kaapana-backend/client/cohort-names")
    with requests.Session() as s:
      r = requests_retry_session(session=s).get('http://kaapana-backend-service.base.svc:5000/client/cohort-names')

    #r = requests.get(f'http://kaapana-backend-service.base.svc:5000/client/cohort-names',verify=False)
    print(r.json)
    print(r)
    return r.json()

@router.get('/buckets')
def listbuckets(minio=Depends(get_minio)):
    """Return List of Minio buckets
    """
    buckets = minio.list_buckets()
    data = []
    for bucket in buckets:
        data.append({
          'name':str(bucket.name),
          'creation_date': bucket.creation_date,
          'webui':f'https://{settings.hostname}/minio/{bucket.name}'
        })
    return data


@router.post('/buckets/{bucketname}')
def makebucket(bucketname: str, minio=Depends(get_minio)):
    """
    To Create a Bucket
    """    
    bucketname = bucketname.lower().strip()
    if minio.bucket_exists(bucketname):
        raise HTTPException(status_code=409, detail=f"Bucket {bucketname} already exists.")
    else:
        minio.make_bucket(bucketname)
        return {}


@router.get('/buckets/{bucketname}')
def listbucketitems(bucketname: str, minio=Depends(get_minio)):
    """
    To List  Bucket Items
    """   
    bucket_items = [] 
    bucketname =  bucketname.lower().strip()
    if minio.bucket_exists(bucketname):
        objects = minio.list_objects(bucketname,recursive=True)
        for obj in objects:
          bucket_items.append({
            'bucket_name': str(obj.bucket_name),
            'object_name': str(obj.object_name),
            'last_modified': obj.last_modified,
            'etag': obj.etag,
            'size': obj.size,
            'type': obj.content_type})      

        return bucket_items
    else:
      raise HTTPException(status_code=404, detail=f"Bucket {bucketname} does not exist")
        
@router.delete('/buckets/{bucketname}')
def removebucket(bucketname: str, minio=Depends(get_minio)):
    """
    To remove a bucket
    """    
    bucketname =  bucketname.lower().strip()

    if minio.bucket_exists(bucketname):
        objects = list(minio.list_objects(bucketname))
        if objects:
          raise HTTPException(status_code=409, detail=f"Bucket {bucketname} not empty")
        else:
          minio.remove_bucket(bucketname)
          return {}
    else:
        raise HTTPException(status_code=404, detail=f"Bucket {bucketname} does not exist")

