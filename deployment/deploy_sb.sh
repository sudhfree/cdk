#!/bin/bash
rm deploy.env
cp ./config/sb.deploy.env deploy.env

rm ../src/api/config/app.env
cp ../src/api/config/sb.app.env ../src/api/config/app.env

echo "starting invoice-service-api deployment..."
cdk deploy --outputs-file outputs.json --require-approval "never" sb-invoice-service

# Run script to dynmically set S3 bucket and Key file name to API AppSettings file app.env  'bucket://projectname/env/app.env
echo "Updating AppSettings..."
python3 export_app_settings.py

rm ../src/base_invoice_adjustment/config/app.env
cp ../src/base_invoice_adjustment/config/sb.app.env ../src/base_invoice_adjustment/config/app.env

rm ../src/base_ns_invoice_notifier/config/app.env
cp ../src/base_ns_invoice_notifier/config/sb.app.env ../src/base_ns_invoice_notifier/config/app.env

echo "starting lambda deployment"
cdk deploy --require-approval "never" sb-invoice-service-adjustment
cdk deploy --require-approval "never" sb-invoice-service-ns-notifier
echo "deployment complete"

