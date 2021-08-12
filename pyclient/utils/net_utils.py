

def isIPv4(address):
    '''
    This code will check if the string is a valid IPv4 address

    Args:
        address (string): the string that will be checked to see if it is a valid IPv4 address

    Return:
        isIP (boolean): whether the address is of the valid IPv4 format
    '''
    isIP = True
    # split the address into groups seperated by "."
    a = address.split('.')
    if len(a) != 4:
        isIP = False
    else: 
        for x in a:
            #checks if each group is a digit between 0 and 255
            if not x.isdigit():
                isIP = False
            i = int(x)
            if i < 0 or i > 255:
                isIP = False
    return isIP