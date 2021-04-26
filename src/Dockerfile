FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7
WORKDIR /invoice_api
COPY . /invoice_api
RUN pip3 install -r requirements.lambda_layer.txt
#EXPOSE 8001
EXPOSE 8080
#RUN  -p 8001:8001 reference_data_api.api_app:api_app env
#RUN  --env-file=env.txt -p 8001:8001 reference_data_api.api_app:api_app env
#RUN  -d  --env-file=env.txt -p 8001:8001 reference_data_api.api_app:api_app env
#RUN  --env-file=env.txt -p 8001:8001 uvicorn reference_data_api.api_app:api_app env
#RUN ["/bin/bash", "-c", "echo hello"]
CMD ["uvicorn", "api.api_app:api_app", "--host", "0.0.0.0", "--port", "8080"]