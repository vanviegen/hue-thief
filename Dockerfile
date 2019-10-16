FROM python:3
RUN git clone https://github.com/vanviegen/hue-thief
RUN pip3 install wheel
RUN pip3 install -r hue-thief/requirements.txt
# for runtime flexibility let's not hard-bake the command into the image
#CMD [ "python3", "hue-thief/hue-thief.py", "/dev/ttyUSB1" ]
