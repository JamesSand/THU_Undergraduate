from __future__ import division
import numpy as np


class EuclideanLoss(object):
    def __init__(self, name):
        self.name = name

    def forward(self, input, target):
        # TODO START
        '''Your codes here'''
        # input & target batch_size * 10
        # output batch_size * 10
        # print("target", target.shape)
        # print("target")
        # print(target)
        # print("output")
        # print(input)
        # print("input", input.shape)
        output = target - input
        output = output ** 2 / 2
        # 获取样本数
        batch_size = output.shape[0]
        # 两次 sum
        output = np.sum(output)
        output = np.sum(output)
        # 除去样本数
        output = output / batch_size
        # print("loss")
        # print(output)
        
        return output
        # TODO END

    def backward(self, input, target):
		# TODO START
        '''Your codes here'''
        #  这一步是第一个 delta 
        output = input - target
        # 之后要除 batch size 所以这里先除掉
        batch_size = output.shape[0]
        output = output / batch_size
        # print("delta0", output)
        # exit(0)
        return output
		# TODO END


class SoftmaxCrossEntropyLoss(object):
    def __init__(self, name):
        self.name = name

    def forward(self, input, target):
        # TODO START
        '''Your codes here'''
        batch_size = input.shape[0]
        predict_size = input.shape[1]

        # 计算 exp sum
        exp = np.exp(input)
        exp_sum = np.sum(exp, axis=1)
        # 复制 10 份，这时候 exp_sum 是 10 * batch_size
        exp_sum = np.tile(exp_sum, (predict_size, 1))
        # 转置之后是 batch_size * 10
        exp_sum = exp_sum.T
        
        h = exp / exp_sum
        # ln_h 的形状是 batch_size * 10
        ln_h = np.log(h)
        # 我们要做 ln_h * target.T 在取对角线元素之和
        sum = np.matmul(ln_h, target.T)
        sum = np.diag(sum)
        # 这一步的 sum 是各个样本的 loss，直接保存
        sum = -sum
        sum = np.sum(sum)
        
        
        output = sum / batch_size
        return output
        # TODO END

    def backward(self, input, target):
        # TODO START
        '''Your codes here'''
        
        batch_size = input.shape[0]
        predict_size = input.shape[1]

        # 算出来的结果是 h_k - t_k
        # 计算 exp sum
        exp = np.exp(input)
        exp_sum = np.sum(exp, axis=1)
        # 复制 10 份，这时候 exp_sum 是 10 * batch_size
        exp_sum = np.tile(exp_sum, (predict_size, 1))
        # 转置之后是 batch_size * 10
        exp_sum = exp_sum.T
        
        h = exp / exp_sum

        output = h - target
        output = output / batch_size

        return output
        # TODO END


class HingeLoss(object):
    def __init__(self, name, margin=5):
        self.name = name
        self.margin = margin

    def forward(self, input, target):
        # TODO START 
        '''Your codes here'''
        # # 取对角线之后就是正确坐标的 预测值
        target_coord = np.matmul(input, target.T)
        target_coord = np.diag(target_coord)

        # 为了能够 广播
        calculate_result = self.margin - target_coord + input.T
        # 再变回来
        calculate_result = calculate_result.T
        calculate_result = np.maximum(0, calculate_result)

        zero_matrix = 1 - target
        output = calculate_result * zero_matrix

        batch_size = input.shape[0]
        output = output / batch_size

        self._saved = output
        return output
        # TODO END

    def backward(self, input, target):
        # TODO START
        '''Your codes here'''

        output = self._saved > 0
        above_matrix = -np.sum(output, axis=1)

        target_matrix = target
        target_matrix = target_matrix.T * above_matrix
        target_matrix = target_matrix.T

        output = output + target_matrix
        batch_size = input.shape[0]
        output = output / batch_size
        return output 
        # TODO END

