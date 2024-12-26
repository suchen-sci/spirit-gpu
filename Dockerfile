FROM megaease/base:cuda11.8.0-v0.0.1

RUN pip3 install vllm
RUN vllm serve NousResearch/Meta-Llama-3-8B-Instruct --dtype auto &

COPY . /workspace 
WORKDIR /workspace
RUN pip3 install .
RUN pip3 install -r requirements.txt

RUN python3.11 ./test/download_data.py

ENTRYPOINT [ "sh" ]
CMD [ "./test/run.sh" ]
