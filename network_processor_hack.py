import os
import re

from networks import createModel


def netToArrayOfTuples(model):
    model.save("auto.net")
    return connectionStringToArrayOfTuples(getConnectionsString("auto.net"))


def getConnectionsString(filePath):
    with open(filePath, "r") as f:
        lines = f.read().splitlines()
        last_line = lines[-1]
        print(last_line)
        return last_line.split("=")[1]


def connectionStringToArrayOfTuples(connections):
    formattedConnections = connections.strip().replace(",", ".").replace(". ", ",")
    tuples = []
    print("Connections:\n{}".format(formattedConnections))
    for t in formattedConnections.split(" "):
        a, b = t.strip("()").split(",")
        tuples.append((int(a), float(b)))
    return tuples


def updateConnectionString(sourceFile, destinationFile, newConnections):
    connectionString = "connections (connected_to_neuron, weight)={}".format(
        newConnections
    )
    with open(sourceFile, "r") as source:
        lines = source.read().splitlines()
        for i in range(1, len(lines)):
            lines[i] = re.sub("\.", ",", lines[i])
        lines[-1] = re.sub("[\[\]]", "", connectionString)
    with open(destinationFile, "w") as destination:
        destination.write("\n\r".join(lines))


def copyModelWithDifferentConnecions(model, newConnections):
    model.save("copy.net")
    updateConnectionString("copy.net", "newcopy.net", newConnections)
    return model.create_from_file("newcopy.net")


model = createModel(3, 1)
con = netToArrayOfTuples(model)
print("Before change:\n{}".format(con))

copyModelWithDifferentConnecions(model, con)
