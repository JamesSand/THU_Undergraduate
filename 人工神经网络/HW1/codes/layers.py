import numpy as np


class Layer(object):
    def __init__(self, name, trainable=False):
        self.name = name
        self.trainable = trainable
        self._saved_tensor = None

    def forward(self, input):
        pass

    def backward(self, grad_output):
        pass

    def update(self, config):
        pass

    def _saved_for_backward(self, tensor):
        '''The intermediate results computed during forward stage
        can be saved and reused for backward, for saving computation'''

        self._saved_tensor = tensor

class Relu(Layer):
    def __init__(self, name):
        super(Relu, self).__init__(name)

    def forward(self, input):
        # TODO START
        '''Your codes here'''
        self._saved_for_backward(input)

        output = np.maximum(0, input)
        return output
        # TODO END

    def backward(self, grad_output):
        # TODO START
        '''Your codes here'''
        input = self._saved_tensor
        above_zero = input > 0
        output = above_zero * grad_output
        return output
        # TODO END

class Sigmoid(Layer):
    def __init__(self, name):
        super(Sigmoid, self).__init__(name)

    def forward(self, input):
        # TODO START
        '''Your codes here'''
        output = 1 / (1 + np.exp(-input))
        self._saved_for_backward(output)
        return output
        # TODO END

    def backward(self, grad_output):
        # TODO START
        '''Your codes here'''
        result = self._saved_tensor
        # 求导结果是 result * (1 - result)
        output = grad_output * result * (1 - result)
        return output
        # TODO END

class Gelu(Layer):
    def __init__(self, name):
        super(Gelu, self).__init__(name)

    def forward(self, input):
        # TODO START
        '''Your codes here'''

        self._saved_for_backward(input)

        inside = 0.044715 * input ** 3 + input
        inside = inside * np.sqrt(2) / np.sqrt(np.pi)
        tanh = np.tanh(inside)
        tanh += 1
        output = tanh * input * 0.5
        return output
        # TODO END
    
    def backward(self, grad_output):
        # TODO START
        '''Your codes here'''
        
        const = 0.044715

        input = self._saved_tensor
        inside = const * input ** 3 + input
        inside = inside * np.sqrt(2) / np.sqrt(np.pi)

        output = 0.5 + 0.5 * np.tanh(inside) + 0.5 * input * (1 - np.tanh(inside) * np.tanh(inside)) * (np.sqrt(2) / np.sqrt(np.pi)) * (1 + 3 * const * input ** 2)
        output = grad_output * output
        return output
        # TODO END

class Linear(Layer):
    def __init__(self, name, in_num, out_num, init_std):
        super(Linear, self).__init__(name, trainable=True)
        self.in_num = in_num
        self.out_num = out_num
        self.W = np.random.randn(in_num, out_num) * init_std
        self.b = np.zeros(out_num)

        self.grad_W = np.zeros((in_num, out_num))
        self.grad_b = np.zeros(out_num)

        self.diff_W = np.zeros((in_num, out_num))
        self.diff_b = np.zeros(out_num)

    def forward(self, input):
        # TODO START
        '''Your codes here'''
        # input 100 * 784 100 个样本 每个 784
        # self.W 784 * 10
        # output 100 * 10
        # self.b 10 * 1
        
        # 为反向传播保存
        self._saved_for_backward(input)

        output = np.matmul(input, self.W)
        output = output + self.b
        return output
        # TODO END

    def backward(self, grad_output):
        # TODO START
        '''Your codes here'''
        # grad_output 是 当前层 + 1 的 delta
        # 最后要返回 当前层的 delta

        # 上一层的输入
        input = self._saved_tensor
        self.grad_W = np.matmul(input.T, grad_output)
        batch_size = grad_output.shape[0]
        one = np.ones(batch_size)
        self.grad_b = np.matmul(one.T, grad_output)

        output = np.matmul(grad_output, self.W.T)
        # print("grad w", self.grad_W.shape)
        # print("grad b", self.grad_b.shape)
        # print("output", output.shape)
        # exit(0)
        return output
        # TODO END

    def update(self, config):
        mm = config['momentum']
        lr = config['learning_rate']
        wd = config['weight_decay']

        self.diff_W = mm * self.diff_W + (self.grad_W + wd * self.W)
        self.W = self.W - lr * self.diff_W

        self.diff_b = mm * self.diff_b + (self.grad_b + wd * self.b)
        self.b = self.b - lr * self.diff_b
