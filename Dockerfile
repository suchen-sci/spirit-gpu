FROM megaease/base:cuda11.8.0-v0.0.1

# 复制目录及其内容
COPY test /workspace/test
WORKDIR /workspace
RUN pip3 install .
RUN pip3 install -r requirements.txt

ENTRYPOINT [ "sh" ]
CMD [ "./test/run.sh" ]
