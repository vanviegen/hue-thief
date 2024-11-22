FROM python:3
COPY *.py requirements.txt .
RUN pip3 install wheel
RUN pip3 install -r requirements.txt
ENTRYPOINT [ "python3", "hue-thief.py" ]
