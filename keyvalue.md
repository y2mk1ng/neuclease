
API for 'keyvalue' datatype (github.com/janelia-flyem/dvid/datatype/keyvalue)
=============================================================================

Note: UUIDs referenced below are strings that may either be a unique prefix of a
hexadecimal UUID string (e.g., 3FA22) or a branch leaf specification that adds
a colon (":") followed by the case-dependent branch name.  In the case of a
branch leaf specification, the unique UUID prefix just identifies the repo of
the branch, and the UUID referenced is really the leaf of the branch name.
For example, if we have a DAG with root A -> B -> C where C is the current
HEAD or leaf of the "master" (default) branch, then asking for "B:master" is
the same as asking for "C".  If we add another version so A -> B -> C -> D, then
references to "B:master" now return the data from "D".

Command-line:

$ dvid repo <UUID> new keyvalue <data name> <settings...>

	Adds newly named key-value data to repo with specified UUID.

	Example:

	$ dvid repo 3f8c new keyvalue stuff

	Arguments:

	UUID           Hexadecimal string with enough characters to uniquely identify a version node.
	data name      Name of data to create, e.g., "myblobs"
	settings       Configuration settings in "key=value" format separated by spaces.

	Configuration Settings (case-insensitive keys):

	Versioned      Set to "false" or "0" if the keyvalue instance is unversioned (repo-wide).
				   An unversioned keyvalue will only use the UUIDs to look up the repo and
				   not differentiate between versions in the same repo.  Note that unlike
				   versioned data, distribution (push/pull) of unversioned data is not defined 
				   at this time.

$ dvid -stdin node <UUID> <data name> put <key> < data

	Puts stdin data into the keyvalue data instance under the given key.

	
	------------------

HTTP API (Level 2 REST):

Note that browsers support HTTP PUT and DELETE via javascript but only GET/POST are
included in HTML specs.  For ease of use in constructing clients, HTTP POST is used
to create or modify resources in an idempotent fashion.

### help

	GET  <api URL>/node/<UUID>/<data name>/help

		Returns data-specific help message.

### info

	GET  <api URL>/node/<UUID>/<data name>/info
	POST <api URL>/node/<UUID>/<data name>/info

		Retrieves or puts data properties.

		Example:

		GET <api URL>/node/3f8c/stuff/info

		Returns JSON with configuration settings.

		Arguments:

		UUID          Hexadecimal string with enough characters to uniquely identify a version node.
		data name     Name of keyvalue data instance.

### tags

	GET <api URL>/node/<UUID>/<data name>/tags
	POST <api URL>/node/<UUID>/<data name>/tags?<options>

		GET retrieves JSON of tags for this instance.
		POST appends or replaces tags provided in POST body.  Expects JSON to be POSTed
		with the following format:

		{ "tag1": "anything you want", "tag2": "something else" }

		To delete tags, pass an empty object with query string "replace=true".

		POST Query-string Options:

		replace   Set to "true" if you want passed tags to replace and not be appended to current tags.
					Default operation is false (append).

### keys

GET  <api URL>/node/<UUID>/<data name>/keys

	Returns all keys for this data instance in JSON format:

	[key1, key2, ...]

GET  <api URL>/node/<UUID>/<data name>/keyrange/<key1>/<key2>

	Returns all keys between 'key1' and 'key2' for this data instance in JSON format:

	[key1, key2, ...]

	Arguments:

	UUID          Hexadecimal string with enough characters to uniquely identify a version node.
	data name     Name of keyvalue data instance.
	key1          Lexicographically lowest alphanumeric key in range.
	key2          Lexicographically highest alphanumeric key in range.

GET  <api URL>/node/<UUID>/<data name>/keyrangevalues/<key1>/<key2>?<options>

	This has the same response as the GET /keyvalues endpoint but a different way of
	specifying the keys.  In this endpoint, you specify a range of keys.  In the other
	endpoint, you must explicitly send the keys in a GET payload, which may not be
	fully supported.

	Note that this endpoint streams data to the requester, which prevents setting HTTP
	status to error if the streaming has already started.  Instead, malformed output
	will inform the requester of an error.

	Response types:

	1) json (values are expected to be valid JSON or an error is returned)

		{
			"key1": value1,
			"key2": value2,
			...
		}

	2) tar

		A tarfile is returned with each keys specifying the file names and
		values as the file bytes.

	3) protobuf3
	
		KeyValue data needs to be serialized in a format defined by the following 
		protobuf3 definitions:

		message KeyValue {
			string key = 1;
			bytes value = 2;
		}

		message KeyValues {
			repeated KeyValue kvs = 1;
		}

	Arguments:

	UUID          Hexadecimal string with enough characters to uniquely identify a version node.
	data name     Name of keyvalue data instance.
	key1          Lexicographically lowest alphanumeric key in range.
	key2          Lexicographically highest alphanumeric key in range.

	GET Query-string Options (only one of these allowed):

	json        If set to "true", the response will be JSON as above and the values must
				  be valid JSON or an error will be returned.
	tar			If set to "true", the response will be a tarfile with keys as file names.
	protobuf	Default, or can be set to "true". Response will be protobuf KeyValues response

	Additional query option:

	check		If json=true, setting check=false will tell server to trust that the
				  values will be valid JSON instead of parsing it as a check.


GET  <api URL>/node/<UUID>/<data name>/key/<key>
POST <api URL>/node/<UUID>/<data name>/key/<key>
DEL  <api URL>/node/<UUID>/<data name>/key/<key> 
HEAD <api URL>/node/<UUID>/<data name>/key/<key> 

	Performs operations on a key-value pair depending on the HTTP verb.  

	Example: 

	GET <api URL>/node/3f8c/stuff/key/myfile.dat

	Returns the data associated with the key "myfile.dat" of instance "stuff" in version
	node 3f8c.

	The "Content-type" of the HTTP response (and usually the request) are
	"application/octet-stream" for arbitrary binary data.

	For HEAD returns:
	200 (OK) if a sparse volume of the given label exists within any optional bounds.
	204 (No Content) if there is no sparse volume for the given label within any optional bounds.

	Arguments:

	UUID          Hexadecimal string with enough characters to uniquely identify a version node.
	data name     Name of keyvalue data instance.
	key           An alphanumeric key.
	
	POSTs will be logged as a Kafka JSON message with the following format:
	{ 
		"Action": "postkv",
		"Key": <key>,
		"Bytes": <number of bytes in data>,
		"UUID": <UUID on which POST was done>
	}

GET <api URL>/node/<UUID>/<data name>/keyvalues[?jsontar=true]
POST <api URL>/node/<UUID>/<data name>/keyvalues

	Allows batch query or ingest of data. 

	KeyValue data needs to be serialized in a format defined by the following protobuf3 definitions:

		message KeyValue {
			string key = 1;
			bytes value = 2;
		}

		message Keys {
			repeated string keys = 1;
		}
		
		message KeyValues {
			repeated KeyValue kvs = 1;
		}
	
	For GET, the query body must include a Keys serialization and a KeyValues serialization is
	returned.

	For POST, the query body must include a KeyValues serialization.
	
	POSTs will be logged as a series of Kafka JSON messages, each with the format equivalent
	to the single POST /key:
	{ 
		"Action": "postkv",
		"Key": <key>,
		"Bytes": <number of bytes in data>,
		"UUID": <UUID on which POST was done>
	}

	Arguments:

	UUID          Hexadecimal string with enough characters to uniquely identify a version node.
	data name     Name of keyvalue data instance.

	GET Query-string Options (only one of these allowed):

	json        If
	jsontar		If set to any value for GET, query body must be JSON array of string keys
				and the returned data will be a tarfile with keys as file names.

	Response types:

	1) json (values are expected to be valid JSON or an error is returned)

		{
			"key1": value1,
			"key2": value2,
			...
		}

	2) tar

		A tarfile is returned with each keys specifying the file names and
		values as the file bytes.

	3) protobuf3
	
		KeyValue data needs to be serialized in a format defined by the following 
		protobuf3 definitions:

		message KeyValue {
			string key = 1;
			bytes value = 2;
		}

		message KeyValues {
			repeated KeyValue kvs = 1;
		}

	Arguments:

	UUID          Hexadecimal string with enough characters to uniquely identify a version node.
	data name     Name of keyvalue data instance.
	key1          Lexicographically lowest alphanumeric key in range.
	key2          Lexicographically highest alphanumeric key in range.

	GET Query-string Options (only one of these allowed):

	json        If set to "true", the response will be JSON as above and the values must
					be valid JSON or an error will be returned.
	tar			If set to "true", the response will be a tarfile with keys as file names.
	protobuf	If set to "true", the response will be protobuf KeyValues response

	check		If json=true, setting check=false will tell server to trust that the
					values will be valid JSON instead of parsing it as a check.
