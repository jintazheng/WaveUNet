import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from modelStruct.utils import *


class Resv2Unetv2(nn.Module):
    def __init__(self,nefilters=24):
        super(Resv2Unetv2, self).__init__()
        print('resv2unetv2')
        nlayers = 12
        self.num_layers = nlayers
        self.nefilters = nefilters
        filter_size = 9
        merge_filter_size = 5
        self.encoder = nn.ModuleList()
        self.decoder = nn.ModuleList()
        #self.downsample=nn.ModuleList()
        #self.upsample = nn.ModuleList()
        #echannelin = [24, 24, 48, 72, 96, 124, 144, 168, 192, 216, 240, 264]
        #echannelout = [24, 48, 72, 96, 124, 144, 168, 192, 216, 240, 264, 288]
        echannelin = [24] + [(i + 1) * nefilters for i in range(nlayers - 1)]
        echannelout = [(i + 1) * nefilters for i in range(nlayers)]
        dchannelin = echannelout[::-1]
        dchannelout = echannelin[::-1]
        #dchannelin = [echannelin[i] + echannelout[i] for i in range(nlayers-1,-1,-1)]
        for i in range(self.num_layers):
            self.encoder.append(BasicBlockV2(echannelin[i],echannelout[i],filter_size,upsample=True))
            #self.downsample.append(BottleneckV2(echannelin[i],echannelout[i],merge_filter_size,stride=2))
            #self.upsample.append(BottleneckV2(dchannelin[i], dchannelin[i],merge_filter_size,upsample=True))
            self.decoder.append(BasicBlockV2(dchannelin[i], dchannelout[i],merge_filter_size,downsample=True))
        self.first = nn.Conv1d(1,24,filter_size,padding=filter_size//2)
        self.middle = BasicBlockV2(echannelout[-1],echannelout[-1],filter_size)
        self.outbatch = nn.BatchNorm1d(nefilters)
        self.out = nn.Conv1d(nefilters,1,1)
    def forward(self,x):
        encoder = list()
        x = self.first(x)
        input = x
        for i in range(self.num_layers):
            x = self.encoder[i](x)
            encoder.append(x)
            x = x[:, :, ::2]
        x = self.middle(x)
        for i in range(self.num_layers):
            x = F.upsample(x,scale_factor=2,mode='linear')
            x = x+encoder[self.num_layers - i - 1]
            x = self.decoder[i](x)
        x = x + input
        x = self.outbatch(x)
        x = F.leaky_relu(x)
        x = self.out(x)
        x = F.tanh(x)
        return x

