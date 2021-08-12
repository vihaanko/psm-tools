def handleErrorResponse(response):
    if (response == 404):
        return "Connection error"
    elif (response == 400):
        return "Bad Request"
    elif (response == 401):
        return "Unauthorized"
    elif (response == 409):
        return "Conflict"
    elif (response == 412):
        return "Precondition failed"
    elif (response == 500):
        return "Internal server error"
    elif (response == 501):
        return "Not implemented"