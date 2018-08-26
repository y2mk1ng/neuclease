import numpy as np
import pandas as pd

from ..util import fetch_file, post_file
from . import dvid_api_wrapper, fetch_generic_json
from .repo import create_instance


@dvid_api_wrapper
def create_tarsupervoxel_instance(server, uuid, instance, sync_instance, extension, tags=[], *, session=None):
    """
    Create a tarsupervoxel instance and sync it to a labelmap instance.

    Args:
        server:
            dvid server, e.g. 'emdata3:8900'
        
        uuid:
            dvid uuid, e.g. 'abc9'
        
        instance:
            dvid tarsupervoxels instance name, e.g. 'segmentation_sv_meshes'
        
        sync_instance:
            dvid labelmap instance name, e.g. 'segmentation',
            to which the tarsupervoxels instance will be synchronized.
        
        extension:
            tarsupervoxels instances store one file per supervoxel,
            and the file extensions for all supervoxels must match.
            For example, mesh files are typically stored with extension 'drc' or 'obj'.
        
        tags:
            Optional 'tags' to initialize the instance with.
    """
    if extension[0] == '.':
        extension = extension[1:]

    create_instance(server, uuid, instance, "tarsupervoxels", versioned=False, tags=tags,
                    type_specific_settings={"Extension": extension}, session=session)
    
    post_tarsupervoxel_sync(server, uuid, instance, sync_instance, session=session)


@dvid_api_wrapper
def post_tarsupervoxel_sync(server, uuid, instance, sync_instance, replace=False, *, session=None):
    r = session.post(f'http://{server}/api/node/{uuid}/{instance}/sync',
                     params={ "replace": str(bool(replace)).lower() },
                     json={ "sync": sync_instance } )
    r.raise_for_status()


@dvid_api_wrapper
def fetch_tarfile(server, uuid, instance, body_id, output=None, *, session=None):
    """
    Fetch a .tar file from a tarsupervoxels instance for the given body,
    and save it to bytes, a file object, or a file path.
    
    Args:
        server:
            dvid server, e.g. 'emdata3:8900'
        
        uuid:
            dvid uuid, e.g. 'abc9'
        
        instance:
            dvid tarsupervoxels instance name, e.g. 'segmentation_sv_meshes'
        
        body_id:
            The body whose supervoxel files will be fetched in the tar.
        
        output:
            If None, tarfile is returned in-memory, as bytes.
            If str, it is interpreted as a path to which the .tar file will be written.
            Otherwise, must be a file object to write the bytes to (e.g. a BytesIO object).
    
    Returns:
        None, unless no output file object/path is provided,
        in which case the tarfile bytes are returned.
    """
    url = f'http://{server}/api/node/{uuid}/{instance}/tarfile/{body_id}'
    return fetch_file(url, output, session=session)


@dvid_api_wrapper
def post_load(server, uuid, instance, tar, *, session=None):
    """
    Load a group of supervoxel files (e.g. .drc files) into the tarsupervoxels filestore.

    Args:
        server:
            dvid server, e.g. 'emdata3:8900'
        
        uuid:
            dvid uuid, e.g. 'abc9'
        
        instance:
            dvid tarsupervoxels instance name, e.g. 'segmentation_sv_meshes'
        
        tar:
            Tarfile contents.  Either a path to a .tar file, a (binary) file object,
            or a bytes object with the contents of a .tar file.
            The tarfile should contain files named with the pattern <supervoxel-id>.<extension>,
            where the extension matches the extension specified in the tarsupervoxels instance metadata.
            For example:1234.drc
            (The tarfile should contain no directories.)
            
        Example:
        
            subprocess.check_call('tar -cf supervoxel-meshes.tar 123.drc 456.drc 789.drc', shell=True)
            post_load('mydvid:8000', 'abc123', 'segmentation_sv_meshes', 'supervoxel-meshes.tar')
    """
    url = f'http://{server}/api/node/{uuid}/{instance}/load'
    if isinstance(tar, str):
        assert tar.endswith('.tar'), "Data to .../load must be a .tar file"
    post_file(url, tar, session=session)


@dvid_api_wrapper
def post_supervoxel(server, uuid, instance, supervoxel_id, sv_file, *, session=None):
    """
    Post a supervoxel file (e.g. a mesh file) to a tarsupervoxels instance.
    
    Args:
        server:
            dvid server, e.g. 'emdata3:8900'
        
        uuid:
            dvid uuid, e.g. 'abc9'
        
        instance:
            dvid tarsupervoxels instance name, e.g. 'segmentation_sv_meshes'
        
        sv:
            The supervoxel ID corresponding to the posted file.
            
        sv_file:
            The file to post.
            Either a path to a file, a (binary) file object, or bytes.
    """
    url = f'http://{server}/api/node/{uuid}/{instance}/supervoxel/{supervoxel_id}'
    post_file(url, sv_file, session=session)


@dvid_api_wrapper
def fetch_supervoxel(server, uuid, instance, supervoxel_id, output=None, *, session=None):
    """
    Fetch an individual supervoxel file from a tarsupervoxels instance,
    and save it to bytes, a file object, or a file path.
    
    Args:
        server:
            dvid server, e.g. 'emdata3:8900'
        
        uuid:
            dvid uuid, e.g. 'abc9'
        
        instance:
            dvid tarsupervoxels instance name, e.g. 'segmentation_sv_meshes'
        
        supervoxel_id:
            The supervoxel ID whose file will be retrieved.
        
        output:
            If None, tarfile is returned in-memory, as bytes.
            If str, it is interpreted as a path to which the file will be written.
            Otherwise, must be a file object to write the bytes to (e.g. a BytesIO object).
    
    Returns:
        None, unless no output file object/path is provided,
        in which case the file bytes are returned.
    """
    url = f'http://{server}/api/node/{uuid}/{instance}/supervoxel/{supervoxel_id}'
    return fetch_file(url, output, session=session)


@dvid_api_wrapper
def fetch_exists(server, uuid, instance, supervoxels, *, session=None):
    """
    Determine if the given supervoxels have files loaded into the given tarsupervoxels instance.
    
    Args:
        server:
            dvid server, e.g. 'emdata3:8900'
        
        uuid:
            dvid uuid, e.g. 'abc9'
        
        instance:
            dvid instance name, e.g. 'segmentation'
        
        supervoxels:
            list of supervoxel IDs for which to look for files.
    
    Returns:
        pd.Series of bool, indexed by supervoxel
    """
    url = f'http://{server}/api/node/{uuid}/{instance}/exists'
    supervoxels = np.asarray(supervoxels, np.uint64)
    exists = fetch_generic_json(url, json=supervoxels.tolist(), session=session)

    result = pd.Series(exists, dtype=bool, index=supervoxels)
    result.name = 'exists'
    result.index.name = 'sv'
    return result

