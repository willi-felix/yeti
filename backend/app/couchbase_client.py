from couchbase.cluster import Cluster, ClusterOptions
from couchbase.auth import PasswordAuthenticator
from couchbase.options import UpsertOptions, GetOptions, RemoveOptions, QueryOptions
from datetime import timedelta
from app.config import COUCHBASE_CONN, COUCHBASE_USER, COUCHBASE_PASS, COUCHBASE_BUCKET
cluster = Cluster(COUCHBASE_CONN, ClusterOptions(PasswordAuthenticator(COUCHBASE_USER, COUCHBASE_PASS)))
bucket = cluster.bucket(COUCHBASE_BUCKET)
collection = bucket.default_collection()
def upsert_archive(key: str, doc: dict, ttl_seconds: int = None):
    if ttl_seconds:
        collection.upsert(key, doc, UpsertOptions(expiry=timedelta(seconds=ttl_seconds)))
    else:
        collection.upsert(key, doc)
def get_archive(key: str):
    try:
        res = collection.get(key, GetOptions())
        return res.content_as[dict]()
    except Exception:
        return None
def remove_archive(key: str):
    try:
        collection.remove(key, RemoveOptions())
        return True
    except Exception:
        return False
def query_archives_by_owner(owner_uid: str, limit: int = 100):
    q = f"SELECT META().id as cbid, a.* FROM `{COUCHBASE_BUCKET}` a WHERE a.owner_uid = $owner_uid LIMIT $limit"
    res = cluster.query(q, QueryOptions(named_parameters={'owner_uid': owner_uid, 'limit': limit}))
    return [r for r in res]
def purge_owner_archives(owner_uid: str):
    q = f"DELETE FROM `{COUCHBASE_BUCKET}` WHERE owner_uid = $owner_uid"
    cluster.query(q, QueryOptions(named_parameters={'owner_uid': owner_uid}))
