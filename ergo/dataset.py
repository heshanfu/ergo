import os
import logging as log

import numpy as np
import pandas as pd

from keras.utils import to_categorical

from ergo.core.utils import clean_if_exist
from ergo.core.optimizer import optimize_dataset
from ergo.core.saver import Saver
from ergo.core.loader import Loader

class Dataset(object):
    @staticmethod 
    def clean(path):
        clean_if_exist(path, ('data-train.csv', 'data-test.csv', 'data-validation.csv'))

    @staticmethod
    def optimize(path, reuse = 0.15, output = None):
        optimize_dataset(path, reuse, output)

    @staticmethod
    def split_row(row, n_labels):
        x = row.values[:,1:]
        y = to_categorical(row.values[:,0], n_labels)
        return x, y

    def __init__(self, path):
        self.path       = os.path.abspath(path)
        self.train_path = os.path.join(self.path, 'data-train.csv')
        self.test_path  = os.path.join(self.path, 'data-test.csv')
        self.valid_path = os.path.join(self.path, 'data-validation.csv')
        self.saver      = Saver(self)
        self.loader     = Loader(self)
        self.n_labels   = 0
        self.train      = None
        self.test       = None
        self.validation = None
        self.X_train    = None
        self.Y_train    = None
        self.X_test     = None
        self.Y_test     = None
        self.X_val      = None
        self.Y_val      = None
        self.X          = None
        self.Y          = None

    def exists(self):
        return os.path.exists(self.train_path) and \
               os.path.exists(self.test_path) and \
               os.path.exists(self.valid_path)

    def _set_xys(self, for_training = True):
        if for_training:
            self.X_train, self.Y_train = Dataset.split_row(self.train, self.n_labels)
            self.X_test,  self.Y_test  = Dataset.split_row(self.test, self.n_labels)
            self.X_val,   self.Y_val   = Dataset.split_row(self.validation, self.n_labels)
        else:
            self.X, self.Y = Dataset.split_row(self.train, self.n_labels)

    def load(self):
        self.loader.load()
        self._set_xys()
    
    def source(self, data, p_test = 0.0, p_val = 0.0):
        # reset indexes and resample data just in case
        dataset = data.sample(frac = 1).reset_index(drop = True)
        # count unique labels on first column
        self.n_labels = len(dataset.iloc[:,0].unique())
        # if both values are zero, we're just loading a single file,
        # otherwise we want to generate training temporary datasets.
        for_training = p_test > 0.0 and p_val > 0.0
        if for_training:
            log.info("generating train, test and validation datasets (test=%f validation=%f) ...", 
                    p_test, 
                    p_val)

            n_tot   = len(dataset)
            n_train = int(n_tot * ( 1 - p_test - p_val))
            n_test  = int(n_tot * p_test)
            n_val   = int(n_tot * p_val)

            self.train      = dataset.head(n_train)
            self.test       = dataset.head(n_train + n_test).tail(n_test)
            self.validation = dataset.tail(n_val)

            self.saver.save()
        else:
            self.train = dataset

        self._set_xys(for_training)
