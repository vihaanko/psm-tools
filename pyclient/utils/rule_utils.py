import sys
# Function to seperate protocol from port in port input
def protoPortRead(port):
    protocol = ""
    portNumber = ""
    for c in port:
        split_port = port.split("/")
        if (len(split_port) == 2):
            protocol = split_port[0]
            portNumber = split_port[1]
        elif (len(split_port) == 1):
            protocol = split_port[0]
        else:
            print("Protocol and port should be entered in the following format: (protocol)/(port number)")
    return (protocol, portNumber)


# Function to validate protocol
def protoPortValid(protocol, portNumber):
    if (portNumber and protocol == "icmp"):
        return (False, "Cannot put port number for icmp protocol")

        return (False, "port number should an integer from 0 to 65535")
    if (protocol != "tcp" and protocol != "udp" and protocol != "icmp"):
        return (False, "Your protocol must be tcp, udp, or icmp")

    if (protocol == "tcp" or protocol == "udp"):
        if portNumber.isnumeric():
            port = int(portNumber)
            if (port <= 0 or port >= 65535):
                return (False, "Invalid port number. Port number has to be between 0 and 65535.")
        else:
            return (False, "Port number must be an integer")

    return (True, "")