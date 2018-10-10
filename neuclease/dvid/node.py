from . import dvid_api_wrapper, fetch_generic_json

@dvid_api_wrapper
def fetch_instance_info(server, uuid, instance, *, session=None):
    """
    Returns the full JSON instance info from DVID
    """
    return fetch_generic_json(f'http://{server}/api/node/{uuid}/{instance}/info', session=session)


@dvid_api_wrapper
def post_commit(server, uuid, note, log=[], *, session=None):
    """
    Commit (a.k.a. lock) the given node with a commit note and optional log.
    Returns the full UUID of the committed node.
    """
    body = { "note": note }
    if log:
        assert isinstance(log, list)
        for item in log:
            assert isinstance(item, str)
        body["log"] = log
    
    r = session.post(f'http://{server}/api/node/{uuid}/commit', json=body)
    r.raise_for_status()
    return r.json()["committed"]


@dvid_api_wrapper
def fetch_commit(server, uuid, *, session=None):
    """
    Returns the locked status (True/False) if the given node.
    
    Returns True if the node is locked.
    """
    r = session.get(f'http://{server}/api/node/{uuid}/commit')
    r.raise_for_status()
    return r.json()["Locked"]
    

@dvid_api_wrapper
def post_branch(server, uuid, branch_name, note, custom_uuid=None, *, session=None):
    """
    Create a branch from the given UUID with the given new branch name.
    Branch name must be unique (not used previously in the repo).
    
    If a custom UUID is provided, it will be used by DVID instead of auto-generating one.
    Note: Providing a custom UUID is unusual and should probably be avoided.

    Returns:
        The uuid of the new node (the start of the new branch).
    """
    body = {"branch": branch_name}
    body["note"] = note

    if custom_uuid:
        body["uuid"] = custom_uuid
        
    r = session.post(f'http://{server}/api/node/{uuid}/branch', json=body)
    r.raise_for_status()
    return r.json()["child"]


@dvid_api_wrapper
def post_newversion(server, uuid, note, custom_uuid=None, *, session=None):
    """
    Creates a new node on the same branch as the given uuid.

    If a custom UUID is provided, it will be used by DVID instead of auto-generating one.
    Note: Providing a custom UUID is unusual and should probably be avoided.

    Returns:
        uuid of the new node
    """
    body = { "note": note }
    if custom_uuid:
        body["uuid"] = custom_uuid
        
    r = session.post(f'http://{server}/api/node/{uuid}/newversion', json=body)
    r.raise_for_status()
    return r.json()["child"]


@dvid_api_wrapper
def post_blob(server, uuid, instance, data=None, json=None, *, session=None):
    """
    Post a 'blob' of arbitrary data to the DVID server's blobstore.
    
    The server will create a reference for the blob, which is returned.
    The reference is a URL-friendly content hash (FNV-128) of the blob data.
    """
    assert (data is not None) ^ (json is not None), "Must provide either data or json (but not both)"
    r = session.post(f'http://{server}/api/node/{uuid}/{instance}/blobstore', data=data, json=json)
    r.raise_for_status()
    
    return r.json()["reference"]


@dvid_api_wrapper
def fetch_blob(server, uuid, instance, reference, as_json=False, *, session=None):
    """
    Fetch a previously-stored 'blob' of data from the DVID server's blobstore.
    
    Blobs are stored by various operations, such as supervoxel splits,
    annotation elements POSTs, and others.
    
    Returns:
        Either bytes or parsed JSON data, depending on as_json.
    """
    r = session.get(f'http://{server}/api/node/{uuid}/{instance}/blobstore/{reference}')
    r.raise_for_status()
    if as_json:
        return r.json()
    return r.content
