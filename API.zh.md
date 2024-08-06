# Serverless APIs

- [Serverless APIs](#serverless-apis)
  - [异步请求](#异步请求)
    - [请求](#请求)
    - [响应](#响应)
    - [Webhook](#webhook)
    - [例子](#例子)
  - [同步请求](#同步请求)
    - [请求](#请求-1)
    - [响应](#响应-1)
    - [例子](#例子-1)
  - [状态](#状态)
    - [请求](#请求-2)
    - [响应](#响应-2)
    - [例子](#例子-2)
  - [请求状态查询](#请求状态查询)
    - [请求](#请求-3)
    - [响应](#响应-3)
      - [响应解释](#响应解释)
        - [statusCode:](#statuscode)
        - [result:](#result)
        - [status:](#status)
      - [总结](#总结)
    - [多个请求状态查询](#多个请求状态查询)
    - [请求](#请求-4)
    - [响应](#响应-4)
  - [清理异步请求](#清理异步请求)
    - [请求](#请求-5)
    - [响应](#响应-5)
    - [例子](#例子-3)
  - [取消特定异步请求](#取消特定异步请求)
    - [请求](#请求-6)
    - [响应](#响应-6)
    - [例子](#例子-4)
  - [请求体](#请求体)
  - [错误处理](#错误处理)


## 异步请求

### 请求
* 路径:`/v1/<your-serverless-id>/async`
* 方法: POST
* 请求头: `Authorization: Bearer <your-api-key>`

请求体:
```json
{
    "input": {},
    "webhook": "<your-webhook-url>"
}
```
- "webhook": 由 worker 用来回传结果。


### 响应
成功响应
```json
{
    "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "sequence": "1234"
}
```
- "id": 请求ID，worker 将使用此 ID 通过 webhook 发送结果。
- "sequence": 用于取消此任务。


### Webhook
worker 将向您的 webhook 发送以下请求：

* 请求参数: "?requestID=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee&statusCode=200"
* 方法: POST
* 请求体: Result from the worker, depending on the template used.


### 例子
```bash
curl -X POST http://localhost:10088/v1/<your-serverless-id>/async \
    -H "Authorization: Bearer <your-api-key>" -d '{"input": {}, "webhook": "xxx"}'
```

## 同步请求

### 请求
* 路径: `/v1/<your-serverless-id>/sync`
* 方法: POST
* 请求头: `Authorization: Bearer <your-api-key>`

请求体: 
```json
{
    "input": {},
}
```

### 响应
成功响应： worker 的结果，依据所用模板而定。



### 例子
```bash
curl -X POST http://localhost:10088/v1/<your-serverless-id>/sync \
    -H "Authorization: Bearer <your-api-key>" -d '{"input": {}}'
```

## 状态

### 请求
* 路径: `/v1/<your-serverless-id>/status`
* 方法: GET
* 请求头: `Authorization: Bearer <your-api-key>`


### 响应
成功响应：
```json
{
    "queueingCount": 10
}
```
- "queueingCount": 该 serverless ID 下尚未处理的任务数量。

### 例子

```bash
curl -X GET http://localhost:10088/v1/<your-serverless-id>/status -H "Authorization: Bearer <your-api-key>"                              
```

## 请求状态查询

### 请求
* 路径: `/v1/<your-serverless-id>/status?requestID=<your-request-id>` 
* 方法: GET
* 请求头: `Authorization: Bearer <your-api-key>`
* 请求体: 无

### 响应

成功响应:
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

#### 响应解释

##### statusCode:

- `200`：代表着请求正在运行或者结束运行。
- `404`：请求状态已经被清理（目前，我们会保存请求状态30min）。
- 其他状态码：代表着有错误发生，请参考 `message` 获取更多详细信息。

##### result:

- 该字段包含以 base64 编码的 worker 结果（与发送到 webhook 的结果一致）。
- 如果 `result` 为 `null` 且 `statusCode` 为 `200`，表示任务仍在进行中。
- 注意: `result` 字段的最大大小为 `2MB`。如果 worker 结果超过此限制，则必须通过 `webhook` 或其他方式获取。
- 
##### status:
- `succeed`: 任务成功完成。
- 对于其他状态，请参考 `message` 字段了解更多信息。

#### 总结
- 如果 `statusCode` 为 `200` 且 `result` 非空，您可以获取结果。
- 如果 `statusCode` 为 `404`，则请求状态已被移除。
- 对于其他 `statusCode` 值，请检查 `message` 和 `status` 字段了解发生了什么。

### 多个请求状态查询

### 请求
* 路径: `/v1/<your-serverless-id>/status` 
* 方法: POST
* 请求头: `Authorization: Bearer <your-api-key>`
* 请求体: 
```
{
    "requestIDs": [<your-request-id1>, <your-request-id2>]
}
```

### 响应

成功响应:
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

更多细节见 [响应解释](#响应解释)

## 清理异步请求

### 请求
* 路径: `/v1/<your-serverless-id>/async`
* 方法: DELETE
* 请求头: `Authorization: Bearer <your-api-key>`

### 响应
成功响应
```json
{
    "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "cleaned": ["aaaaaaaa-bbbb-cccc-dddd-ffffffffffff"]
}
```
- "id": 请求 ID。
- "cleaned": 清理的请求 ID 数组。

### 例子
```bash
curl -X DELETE http://localhost:10088/v1/<your-serverless-id>/async \
    -H "Authorization: Bearer serverless-apikey"
```

## 取消特定异步请求

### 请求
* 路径: `/v1/<your-serverless-id>/async`
* 方法: DELETE
* 请求头: `Authorization: Bearer <your-api-key>`
* 请求参数: `?requestID=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee&sequence=1234`

> `requestID` 和 `sequence` 可以在异步请求的响应中找到。

### 响应
成功响应
```json
{
    "id": "aaaaaaaa-bbbb-cccc-dddd-gggggggggggg",
}
```
- "id": 请求 ID。


### 例子
```bash
curl -X DELETE \ 
    http://localhost:10088/v1/<your-serverless-id>/async?requestID=<request-id>&sequence=<sequence> \
    -H "Authorization: Bearer serverless-apikey"
```

## 请求体

```json
{
    "input": {},
    "webhook": {},
    "policy": {
        "ttl": 600000
    }
}
```

- "ttl": 请求的生存时间，以毫秒为单位。默认情况下，`同步请求`将最多等待3分钟；`异步请求`将等待10分钟。之后，worker 将不再处理请求并将其丢弃。例如，如果只有一个 worker 但同时收到许多请求时，可能会发生这种情况。

## 错误处理

如果状态码不是200，则表示发生了错误。响应体将包含错误信息：

```
{
    "error": "error message"
}
```

错误代码和描述如下：

| 代码 | 消息                                                                                | 描述                                                     |
| ---- | ----------------------------------------------------------------------------------- | -------------------------------------------------------- |
| 400  | "request body too large"                                                            | 请求体必须小于或等于20MB。                               |
| 400  | "failed to get request data"                                                        | 读取请求体时遇到错误。                                   |
| 400  | "invalid request data, must be a json object with 'input' and 'webhook' (optional)" | 请求体必须是一个有效的JSON对象，包含"input"字段。        |
| 400  | "webhook is empty for async request"                                                | 异步请求需要一个webhook。                                |
| 400  | "invalid request arguments"                                                         | 核查请求以确保您使用正确的参数。                         |
| 408  | "request timeout"                                                                   | 同步请求在指定时间内未返回结果。                         |
| 500  | "failed to publish message"                                                         | 服务器内部出错，请稍后再试。                             |
| 500  | "failed to get status"                                                              | 服务器内部出错，请稍后再试。                             |
| 500  | "failed to cancel message(s)"                                                       | 服务器内部出错，请稍后再试。                             |
| 500  | "failed to handle message {request id}: {err}"                                      | worker 处理消息时出现错误。错误详情将在 "{err}" 中指定。 |
| 503  | "not enough gpu now, please try again later"                                        | 目前没有可用的GPU。此消息仅在同步请求时返回。            |


