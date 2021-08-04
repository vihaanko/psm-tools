def saveBinary(path, data):
    with open(path, 'wb') as out_file:       
        out_file.write(data)