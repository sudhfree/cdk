class SecretsManagerConfigurationException(Exception):
    error_code = 1
    status_code = 500
    message = "SecretsManager configuration error."
    pass
