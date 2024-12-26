FROM megaease/base:cuda11.8.0-v0.0.1

RUN pip3 install vllm

COPY Qwen2.5-3B-Instruct /workspace/Qwen2.5-3B-Instruct

COPY API.md /workspace/API.md
COPY API.zh.md /workspace/API.zh.md
COPY Dockerfile /workspace/Dockerfile
COPY LICENSE /workspace/LICENSE
COPY pyproject.toml /workspace/pyproject.toml
COPY README.md /workspace/README.md
COPY requirements.txt /workspace/requirements.txt
COPY setup.py /workspace/setup.py
COPY test.sh /workspace/test.sh


# 复制目录及其内容
COPY spirit_gpu /workspace/spirit_gpu
COPY test /workspace/test
COPY .git /workspace/.git
WORKDIR /workspace
RUN pip3 install .
RUN pip3 install -r requirements.txt

ENTRYPOINT [ "sh" ]
CMD [ "./test/run.sh" ]
