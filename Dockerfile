FROM megaease/base:cuda11.8.0-v0.0.1

RUN pip3 install vllm

COPY Qwen2.5-3B-Instruct /workspace/Qwen2.5-3B-Instruct

COPY . /workspace
WORKDIR /workspace
RUN pip3 install .
RUN pip3 install -r requirements.txt

ENTRYPOINT [ "sh" ]
CMD [ "./test/run.sh" ]
