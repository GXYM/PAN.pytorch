# -*- coding: utf-8 -*-
# @Time    : 2019/8/23 22:00
# @Author  : zhoujun

from __future__ import print_function
import os
from utils import load_json

config = load_json('config.json')
os.environ['CUDA_VISIBLE_DEVICES'] = ','.join([str(i) for i in config['trainer']['gpus']])

from models import get_model, get_loss, get_model_pse1
from data_loader import get_dataloader
from trainer import Trainer


def main(config):
    train_loader, eval_loader = get_dataloader(config['data_loader']['type'], config['data_loader']['args'])

    criterion = get_loss(config).cuda()

    model = get_model(config)

    config['name'] = config['name'] + '_' + model.name
    trainer = Trainer(config=config,
                      model=model,
                      criterion=criterion,
                      train_loader=train_loader)
    trainer.train()


if __name__ == '__main__':
    main(config)
