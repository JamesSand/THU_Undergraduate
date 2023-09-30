# -*- coding: utf-8 -*-

import torch
from torch import nn
from torch.nn import init
from torch.nn.parameter import Parameter
class BatchNorm2d(nn.Module):
	# TODO START
	def __init__(self, num_features, eps=1e-5, mome1=0.8, mome2=0.8):
		super(BatchNorm2d, self).__init__()
		self.num_features = num_features

		# Parameters
		self.weight = nn.Parameter(torch.ones(num_features))
		self.bias = nn.Parameter(torch.zeros(num_features))

		# Store the average mean and variance
		self.register_buffer('running_mean', torch.zeros(num_features))
		self.register_buffer('running_var', torch.ones(num_features))


		# Initialize your parameter
		self.eps = eps
		self.mome1 = mome1
		self.mome2 = mome2

	def get_mean_and_var(self, inputs: torch.Tensor):
		return inputs.mean(dim=0), inputs.var(dim=0)

	def forward(self, input):
		# input: [batch_size, num_feature_map, height, width]
		training_mode = self.training

		if not training_mode:
			return (input-self.running_mean.unsqueeze(0).unsqueeze(-1).unsqueeze(-1))/torch.sqrt(self.eps+self.running_var.unsqueeze(0).unsqueeze(-1).unsqueeze(-1))*self.weight.unsqueeze(0).unsqueeze(-1).unsqueeze(-1)+self.bias.unsqueeze(0).unsqueeze(-1).unsqueeze(-1)
		else:
			batch_size, num_feature, height, width = input.shape
			input = input.permute(0, 2, 3, 1)
			input = input.reshape(-1, num_feature)
			input_mean, input_var = self.get_mean_and_var(input)

			self.running_mean = self.running_mean * \
				self.mome1+(1-self.mome1)*input_mean
			self.running_var = self.running_var * \
				self.mome2+(1-self.mome2)*input_var
			input = input.reshape(batch_size,  height,
									width, num_feature).permute(0, 3, 1, 2)
			input_mean = input_mean.unsqueeze(0).unsqueeze(-1).unsqueeze(-1)
			input_var = input_var.unsqueeze(0).unsqueeze(-1).unsqueeze(-1)

			return (input-input_mean)/torch.sqrt(self.eps+input_var)*self.weight.unsqueeze(0).unsqueeze(-1).unsqueeze(-1)+self.bias.unsqueeze(0).unsqueeze(-1).unsqueeze(-1)

	# TODO END

class Dropout(nn.Module):
	# TODO START
	def __init__(self, p=0.5):
		super(Dropout, self).__init__()
		self.p = p

	def forward(self, input):
        # input: [batch_size, num_feature_map, height, width]
		dp = torch.bernoulli(torch.ones(
			size=(input.shape[0], input.shape[1], 1, 1))*(1-self.p)).to(input.device)
		if not self.training:
			return input
		else:
			return dp*input/(1-self.p)
	# TODO END

class Model(nn.Module):
	def __init__(self, drop_rate=0.5):
		super(Model, self).__init__()
		# TODO START
		# Define your layers here
		self.model_list_1 = nn.ModuleList([
            nn.Conv2d(in_channels = 3, out_channels = 128,
                      kernel_size = 5),
            BatchNorm2d(128),
            nn.ReLU(),
            Dropout(drop_rate),
            nn.MaxPool2d(2),
            nn.Conv2d(in_channels = 128,
                      out_channels = 64 , kernel_size = 3),
            BatchNorm2d(64),
            nn.ReLU(),
            Dropout(drop_rate),
            nn.MaxPool2d(2),
        ])
		self.model_list_2 = nn.ModuleList(
			[nn.Linear(64 * 6 * 6, 10)])
		# TODO END
		self.loss = nn.CrossEntropyLoss()

	def forward(self, x, y=None):
		# TODO START
		# the 10-class prediction output is named as "logits"
		for sub_module in self.model_list_1:
			x = sub_module(x)
		x = x.reshape(x.shape[0], -1)
		for sub_module in self.model_list_2:
			x = sub_module(x)
		logits = x
		# TODO END

		pred = torch.argmax(logits, 1)  # Calculate the prediction result
		if y is None:
			return pred
		loss = self.loss(logits, y)
		correct_pred = (pred.int() == y.int())
		acc = torch.mean(correct_pred.float())  # Calculate the accuracy in this mini-batch

		return loss, acc
