
# Function to seperate protocol from port in port input
def portRead(port):
    protocol = ""
    portNumber = ""
    for c in port:
        for i in c.split():
            if (i.isdigit()):
                portNumber += i
            elif (i != "/"):
                protocol += i
    return (protocol, portNumber)


# Function to validate protocol
def portValid(protocol, portNumber):
    if (portNumber and protocol == "icmp"):
        return (False, "Cannot put port number for icmp protocol")

    if (protocol != "tcp" and protocol != "udp" and protocol != "icmp"):
        return (False, "Your protocol must be tcp, udp, or icmp")

    if (protocol == "tcp" or protocol == "udp"):
        port = int(portNumber)
        if (port <= 0 or port >= 65535):
            return (False, "Invalid port number. Port number has to be between 0 and 65535.")

    return (True, "")