# Serverless APIs

- [Serverless APIs](#serverless-apis)
  - [Async Request](#async-request)
    - [Request](#request)
    - [Response](#response)
    - [Webhook](#webhook)
    - [Example](#example)
  - [Sync Request](#sync-request)
    - [Request](#request-1)
    - [Response](#response-1)
    - [Example](#example-1)
  - [Status of Serverless](#status-of-serverless)
    - [Request](#request-2)
    - [Response](#response-2)
    - [Example](#example-2)
  - [Status of Request](#status-of-request)
    - [Request](#request-3)
    - [Response](#response-3)
      - [Response Explanation](#response-explanation)
        - [statusCode:](#statuscode)
        - [result:](#result)
        - [status:](#status)
      - [Response Summary](#response-summary)
    - [Status of Batch Requests](#status-of-batch-requests)
    - [Request](#request-4)
    - [Response](#response-4)
  - [Clean Async Requests](#clean-async-requests)
    - [Request](#request-5)
    - [Response](#response-5)
    - [Example](#example-3)
  - [Cancel Async Request](#cancel-async-request)
    - [Request](#request-6)
    - [Response](#response-6)
    - [Example](#example-4)
  - [More about Request Body](#more-about-request-body)
  - [Error](#error)


## Async Request

### Request
* path: `/v1/<your-serverless-id>/async`
* method: POST
* header: `Authorization: Bearer <your-api-key>`

request body: 
```json
{
    "input": {},
    "webhook": "<your-webhook-url>"
}
```
- "webhook" is used by the worker to send the result back.


### Response
success response:
```json
{
    "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "sequence": "1234"
}
```
- "id": Request ID; the worker uses this ID to send the result to the webhook.
- "sequence": Used to cancel this task.


### Webhook
The worker will send the following request to your webhook:

* query: "?requestID=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee&statusCode=200"
* method: POST
* body: Result from the worker, depending on the template used.


### Example
```bash
curl -X POST http://localhost:10088/v1/<your-serverless-id>/async \
    -H "Authorization: Bearer <your-api-key>" -d '{"input": {}, "webhook": "xxx"}'
```

## Sync Request

### Request
* path: `/v1/<your-serverless-id>/sync`
* method: POST
* header: `Authorization: Bearer <your-api-key>`

request body: 
```json
{
    "input": {},
}
```

### Response
Success Response: Result from the worker, depending on the template used.



### Example
```bash
curl -X POST http://localhost:10088/v1/<your-serverless-id>/sync \
    -H "Authorization: Bearer <your-api-key>" -d '{"input": {}}'
```

## Status of Serverless

### Request
* path: `/v1/<your-serverless-id>/status`
* method: GET
* header: `Authorization: Bearer <your-api-key>`
* body: no body required


### Response
success response:
```json
{
    "queueingCount": 10
}
```
- "queueingCount": Number of tasks not yet processed for this serverless ID.

### Example

```bash
curl -X GET http://localhost:10088/v1/<your-serverless-id>/status -H "Authorization: Bearer <your-api-key>"                              
```

## Status of Request

### Request
* path: `/v1/<your-serverless-id>/status?requestID=<your-request-id>` 
* method: GET
* header: `Authorization: Bearer <your-api-key>`
* body: no body required

### Response

success response:
```
{
    "statusCode": 200,
    "serverlessID": <your-serverless-id>,
    "requestID": <your-request-id>,
    "status": "succeed",
    "message": <message>,
    "result": <base64 result from worker>
}
```

#### Response Explanation

##### statusCode:

- `200`: The request is either running or has finished successfully.
- `404`: The request status has been removed due to our result retention policy (currently, results are retained for 30 minutes).
- Other codes: An error occurred. Refer to the `message` for more details.

##### result:

- This field contains the worker's result encoded in base64 (same as the one you get from webhook).
- If the result is `null` and statusCode is `200`, the task is still in progress.
- Note: The maximum size for the result field is `2MB`. If the worker's result exceeds this limit, it must be retrieved via webhook or another method.

##### status:
- `succeed`: The task completed successfully.
- For any other status, refer to the `message` field for additional information.

#### Response Summary
If `statusCode` is `200` and result is not `null`, you can retrieve the result.
If `statusCode` is `404`, the request status has been removed.
For other `statusCode` values, check the `message` and `status` fields for details on what occurred.

### Status of Batch Requests

### Request
* path: `/v1/<your-serverless-id>/status` 
* method: POST
* header: `Authorization: Bearer <your-api-key>`
* body: 
```
{
    "requestIDs": [<your-request-id1>, <your-request-id2>]
}
```

### Response

success response:
```
{
    "statuses": [
        {
            "statusCode": 200,
            "serverlessID": <your-serverless-id>,
            "requestID": <your-request-id1>,
            "status": "succeed",
            "message": <message>,
            "result": <base64 result from worker>
        },
        {
            "statusCode": 200,
            "serverlessID": <your-serverless-id>,
            "requestID": <your-request-id2>,
            "status": "succeed",
            "message": <message>,
            "result": <base64 result from worker>
        }
    ]
}
```

See detail explanation in [Response Explanation](#response-explanation)


## Clean Async Requests

### Request
* path: `/v1/<your-serverless-id>/async`
* method: DELETE
* header: `Authorization: Bearer <your-api-key>`
* body: no body

### Response
success response:
```json
{
    "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "cleaned": ["aaaaaaaa-bbbb-cccc-dddd-ffffffffffff"]
}
```
- "id": Request ID.
- "cleaned": Array of cleaned request IDs.

### Example
```bash
curl -X DELETE http://localhost:10088/v1/<your-serverless-id>/async \
    -H "Authorization: Bearer serverless-apikey"
```

## Cancel Async Request

### Request
* path: `/v1/<your-serverless-id>/async`
* method: DELETE
* header: `Authorization: Bearer <your-api-key>`
* query: `?requestID=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee&sequence=1234`
* body: no body

> `requestID` and `sequence` can be find in response of async request.

### Response
success response:
```json
{
    "id": "aaaaaaaa-bbbb-cccc-dddd-gggggggggggg",
}
```
- "id": Request ID.


### Example
```bash
curl -X DELETE \ 
    http://localhost:10088/v1/<your-serverless-id>/async?requestID=<request-id>&sequence=<sequence> \
    -H "Authorization: Bearer serverless-apikey"
```

## More about Request Body

```json
{
    "input": {},
    "webhook": {},
    "policy": {
        "ttl": 600000
    }
}
```

- "ttl": Time to live for the request in milliseconds. By default, a `sync` request will wait for a maximum of 3 minutes; an `async` request will wait for 10 minutes. After that, the worker will no longer process the request and will drop it. This may happen, for example, if there is only one worker but many requests arrive simultaneously.


## Error

If the status code is not `200`, it indicates an error. The body will contain an error message:

```
{
    "error": "error message"
}
```

Following are details:

| code | message                                                                             | description                                                                                                            |
| ---- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| 400  | "request body too large"                                                            | The request body must be less than or equal to 20MB.                                                                   |
| 400  | "failed to get request data"                                                        | An error occurred while reading the request body.                                                                      |
| 400  | "invalid request data, must be a json object with 'input' and 'webhook' (optional)" | The request body must be a valid JSON object with "input" field.                                                       |
| 400  | "webhook is empty for async request"                                                | A webhook is required for asynchronous requests.                                                                       |
| 400  | "invalid request arguments"                                                         | Verify the request against this document to ensure you are using the correct arguments.                                |
| 408  | "request timeout"                                                                   | The synchronous request did not return a result within the specified time.                                             |
| 500  | "failed to publish message"                                                         | There was an internal server error; please try again later.                                                            |
| 500  | "failed to get status"                                                              | There was an internal server error; please try again later.                                                            |
| 500  | "failed to cancel message(s)"                                                       | There was an internal server error; please try again later.                                                            |
| 500  | "failed to handle message {request id}: {err}"                                      | An error occurred while processing the message by worker. The error details are specified in `{err}`.                  |
| 503  | "not enough gpu now, please try again later"                                        | There are currently no GPUs available. Please try again later. This message is only returned for synchronous requests. |


