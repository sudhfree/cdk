#FROM centos:7

#RUN yum install curl -y && curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.32.0/install.sh | bash && . ~/.nvm/nvm.sh && nvm install 14.15.3 && npm i -g aws-cdk typescript && npm i
##RUN yum install python3 -y
#WORKDIR temp
#COPY . .
FROM nikolaik/python-nodejs

USER root
RUN chmod a+rw /
RUN npm version
RUN python --version
RUN npm -g install aws-cdk
RUN cdk version
WORKDIR temp

COPY . .