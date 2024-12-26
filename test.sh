# variable api_key
SERVERLESS_ID="f1d97c0d2531"
API_KEY="f3aa4d6aba3446c89ea840032a32726c"


curl -H "Authorization: ${SERVERLESS_ID}-${API_KEY}" https://testapi.serverless.megaease.cn/api/generate -d '{
  "model": "llama3.2",
  "prompt": "1+1=? explain to me why and show me the steps and every detail that i should know", "stream": false
}'

curl -H "Authorization: ${SERVERLESS_ID}-${API_KEY}" https://testapi.serverless.megaease.cn/api/tags
