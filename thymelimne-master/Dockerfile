# https://www.youtube.com/watch?v=wrMJoKpK2mk
# init a base image (Alpine is small Linux distro)
FROM python:3.8.1-slim
# define the present working directory
WORKDIR /thymelimne
# copy the contents into the working dir
ADD . /thymelimne
# run pip to install the dependencies of the flask app
RUN pip install -r requirements.txt
# define the command to start the container
CMD ["python","app.py"]
