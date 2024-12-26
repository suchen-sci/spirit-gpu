FROM megaease/base:cuda11.8.0-v0.0.1

RUN pip3 install vllm

COPY . /workspace 
WORKDIR /workspace
RUN pip3 install .
RUN pip3 install -r requirements.txt

ENTRYPOINT [ "sh" ]
CMD [ "./test/run.sh" ]
