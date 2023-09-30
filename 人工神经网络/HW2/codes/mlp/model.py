# -*- coding: utf-8 -*-

import torch
from torch import nn
from torch.nn import init
from torch.nn.parameter import Parameter
class BatchNorm1d(nn.Module):
	# TODO START
	def __init__(self, num_features,eps=1e-5,mome1=0.8,mome2=0.9):
		super(BatchNorm1d, self).__init__()
		self.num_features = num_features

		# Parameters
		self.weight = nn.Parameter(torch.ones(num_features))
		self.bias =nn.Parameter(torch.ones(num_features))

		# Store the average mean and variance
		self.register_buffer('running_mean', torch.ones(num_features))
		self.register_buffer('running_var', torch.ones(num_features))
		
		
		# Initialize your parameter
		self.mome1=mome1
		self.mome2=mome2
		self.eps=eps

	def get_mean_and_var(self,inputs):
		return inputs.mean(dim=0),inputs.var(dim=0)

	def forward(self, input):
		# input: [batch_size, num_feature_map * height * width]
		training_mode=self.training

		if training_mode:
			mean_value,var_value=self.get_mean_and_var(input)
			self.running_mean=self.running_mean*self.mome1+(1-self.mome1)*mean_value
			self.running_var=self.running_var*self.mome2+(1-self.mome2)*var_value
			return (input-mean_value)/torch.sqrt(self.eps+var_value)*self.weight+self.bias

		else:
			return (input-self.running_mean)/torch.sqrt(self.eps+self.running_var)*self.weight+self.bias

	# TODO END

class Dropout(nn.Module):
	# TODO START
	def __init__(self, p=0.5):
		super(Dropout, self).__init__()
		self.p = p

	def forward(self, input):
		# input: [batch_size, num_feature_map * height * width]
		training_mode=self.training
		if not training_mode:
			return input
		else:
			dp=torch.bernoulli(torch.ones_like(input)*(1-self.p))
			return dp*input/(1-self.p)
	# TODO END

class Model(nn.Module):
	def __init__(self, drop_rate=0.5):
		super(Model, self).__init__()
		# TODO START
		# Define your layers here
		# modify parameter of nn here if need
		self.model_list=nn.ModuleList([
			nn.Linear(32 * 32 * 3, 100),
			BatchNorm1d(100),
			nn.ReLU(),
			Dropout(drop_rate),
			nn.Linear(100 , 10),
		])

		# TODO END
		self.loss = nn.CrossEntropyLoss()

	def forward(self, x, y=None):
		# TODO START
		# the 10-class prediction output is named as "logits"
		for sub_module in self.model_list:
			x=sub_module(x)
		logits = x
		# TODO END

		pred = torch.argmax(logits, 1)  # Calculate the prediction result
		if y is None:
			return pred
		loss = self.loss(logits, y)
		correct_pred = (pred.int() == y.int())
		acc = torch.mean(correct_pred.float())  # Calculate the accuracy in this mini-batch

		return loss, acc
