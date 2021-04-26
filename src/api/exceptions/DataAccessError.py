class DataAccessError(Exception):
    error_code = 1
    status_code = 500
    message = "Data Access Error"

    def __init__(self, objectType="not specified", id="not specified", message="Data Access Error"):
        self.message = message+" object type {}, with ID = {{".format(objectType, id)
        super().__init__(self.message)

    def __str__(self):
        return self.message