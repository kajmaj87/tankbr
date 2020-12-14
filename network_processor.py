import numpy as np


class Model:
    def __init__(self, parameters, architecture):
        self.parameters = parameters
        self.architecture = architecture

    def run(self, x):
        return full_forward_propagation(x, self.parameters, self.architecture)


def create_model(layers, seed=1, random_scale=0.1):
    architecture = []
    for i in range(1, len(layers)):
        architecture.append(
            {
                "input_dim": layers[i - 1],
                "output_dim": layers[i],
                "activation": "relu" if i - 1 < len(layers) else "sigmoid",
            }
        )
    return Model(init_layers(architecture, seed, random_scale), architecture)


def init_layers(nn_architecture, seed=1, random_scale=0.1):
    np.random.seed(seed)
    params_values = {}

    for i, layer in enumerate(nn_architecture):
        layer_input_size = layer["input_dim"]
        layer_output_size = layer["output_dim"]
        params_values["W" + str(i)] = np.random.randn(layer_output_size, layer_input_size) * random_scale
        params_values["b" + str(i)] = np.random.randn(layer_output_size, 1) * random_scale

    return params_values


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def relu(x):
    return np.maximum(0, x)


def single_layer_forward_propagation(previous_activation, weights, bias, activation="relu"):
    # calculation of the input value for the activation function
    intermediate = np.dot(weights, previous_activation) + bias

    # selection of activation function
    if activation == "relu":
        activation_func = relu
    elif activation == "sigmoid":
        activation_func = sigmoid
    else:
        raise Exception("Non-supported activation function")

    # return of calculated activation A and the intermediate Z matrix
    return activation_func(intermediate)


def full_forward_propagation(x, params_values, nn_architecture):
    # X vector is the activation for layer 0
    current_activation = x

    for i, layer in enumerate(nn_architecture):
        # transfer the activation from the previous iteration
        previous_activation = current_activation

        activation_function = layer["activation"]
        weights = params_values["W" + str(i)]
        bias = params_values["b" + str(i)]
        current_activation = single_layer_forward_propagation(previous_activation, weights, bias, activation_function)

    return current_activation
