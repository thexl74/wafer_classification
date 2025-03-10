# -*- coding: utf-8 -*-
"""train_module.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1l0-yJH27mf3MBuedm9OkyvV9hWl1kMUy
"""

# !gdown --id 1RjprBx8pAjdfPTIifW_xm9SNb0lECfzm -O wafer_processed.zip
#
# !unzip -qq wafer_processed.zip

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf

# -*- CONFIGUREATIONS -*- 
NAME = 'model2'
IMAGE_SIZE = 32   # 32, 16
LEARNING_RATE = 0.001   # 0.01, 0.001, 0.0001 
EARLY_STOPPING = 50
EPOCHS = 1000
BALANCED = False # True이면 train batch 뽑을 때 y가 골고루 나오도록 한다.
ARCH = 1
PATH = 'model2'

# data_generator.py
import numpy as np
import keras
import random
import os

class DataGenerator(keras.utils.Sequence):
  def __init__(self, X, Y, batch_size=32, 
               shuffle=True, augment=True, 
               balanced=False, verbose=0):
    self.shuffle = shuffle
    self.augment = augment
    self.batch_size = batch_size
    self._X = X
    self._Y = Y
    self._verbose = verbose
    self.balanced = balanced
    if self.balanced:
      self.setup_y_map()
    self.on_epoch_end()

  def ratate_image(self, image):
    v = np.random.rand() # 0 ~ 1
    if v < 0.125:
      if self._verbose:
        print("Augment - rotate90")
      return np.rot90(image)
    elif v < 0.25:
      if self._verbose:
        print("Augment - rotate180")
      return np.rot90(image, 2)
    elif v < 0.375:
      if self._verbose:
        print('Augment - rotate270')
      return np.rot90(image, 3)
    elif v < 0.5:
      if self._verbose:
        print('Not Augment')
      return image
    elif v < 0.625:
      if self._verbose:
        print("Augment - rotate90 & Flip left right")
      return np.fliplr(np.rot90(image))
    elif v < 0.75:
      if self._verbose:
        print("Augment - rotate180 & Flip left right")
      return np.fliplr(np.rot90(image, 2))
    elif v < 0.875:
      if self._verbose:
        print('Augment - rotate270 & Flip left right')
      return np.fliplr(np.rot90(image, 3))
    else:
      if self._verbose:
        print('Augment -  Flip left right')
      return np.fliplr(image)

  def augment_x(self, x):
    return self.ratate_image(x)

  def __len__(self):
    return int(np.ceil(len(self._X) / self.batch_size))
    
  def __getitem__(self, index):
    batch_X = None
    batch_Y = None
    if self.balanced:
      batch_X = np.zeros((self.batch_size, *self._X.shape[1:]), dtype=self._X.dtype)
      batch_Y = np.zeros((self.batch_size, *self._Y.shape[1:]), dtype=self._Y.dtype)
      for idx in range(self.batch_size):
        y = random.choice(list(self._y_map.keys()))
        selected_idx = random.choice(self._y_map[y])
        batch_X[idx, :] = self._X[selected_idx, :]
        batch_Y[idx, :] = self._Y[selected_idx, :]
    else:
      indexes = self.indexes[index * self.batch_size : (index+1) * self.batch_size]
      batch_X = self._X[indexes]
      batch_Y = self._Y[indexes]
    
    if self.augment:
      batch_X = batch_X.copy()
      for row in range(len(batch_X)):
        batch_X[row] = self.augment_x(batch_X[row])

    return batch_X, batch_Y

  def setup_y_map(self):
    if self.balanced == False:
      return
    self._y_map = {}
    for idx in range(len(self._Y)):
      y = np.argmax(self._Y[idx])
      if y not in self._y_map:
        self._y_map[y] = []
      self._y_map[y].append(idx)

  def on_epoch_end(self):
    self.indexes = np.arange(len(self._X))
    if self.balanced == False and self.shuffle == True:
      np.random.shuffle(self.indexes)

def read_xy(pickle_path):
  df = pd.read_pickle(pickle_path)
  X = np.array(list(df['waferMap'].values), dtype=np.float32)
  Y = df['failureNum'].values
  return X, Y

x_train, y_train = read_xy('data/wafer_train_{}.pkl'.format(IMAGE_SIZE))

print('x_train.shape:', x_train.shape)
print('y_train.shape:', y_train.shape)

x_valid, y_valid = read_xy('data/wafer_valid_{}.pkl'.format(IMAGE_SIZE))

print('valid_X.shape:', x_valid.shape)
print('valid_Y.shape:', y_valid.shape)

x_test, y_test = read_xy('data/wafer_test_{}.pkl'.format(IMAGE_SIZE))

import numpy

class OneHotHelper:
  '일반 형태 <-> One Hot 형태'
  def __init__(self, labels=[]):
    self._labels = labels

  @property
  def labels(self):
    return self._labels
  
  @property
  def num_labels(self):
    return len(self._labels)

  def transform(self, normal_form):
    result = numpy.zeros((len(normal_form), self.num_labels), dtype=int)

    for row in range(len(normal_form)):
      value = normal_form[row]
      idx = self.labels.index(value)
      result[row, idx] = 1
    return result

  def recover(self, onehot_form):
    result = list()

    for row in range(len(onehot_form)):
      onehot = onehot_form[row]
      idx = numpy.argmax(onehot)
      result.append(self.labels[idx])
    return np.array(result)

def test_onehot():
  labels = ['Hi', 'Hello', 'World']
  helper = OneHotHelper(labels)
  result = helper.transform(['Hello', 'Hi', 'World', 'Hello'])
  print(result)
  recovered = helper.recover(result)
  print(recovered)

  labels = [0, 1, 2, 3, 4, 5, 6]
  helper = OneHotHelper(labels)
  result = helper.transform([6, 1, 2, 4, 4])
  print(result)
  recovered = helper.recover(result)
  print(recovered)

# test_onehot()

onehot_helper = OneHotHelper(labels=[0, 1, 2, 3, 4, 5, 6, 7, 8])
y_train_onehot = onehot_helper.transform(y_train)
y_valid_onehot = onehot_helper.transform(y_valid)

dataset = DataGenerator(x_train, y_train, batch_size=1, shuffle=False, verbose=1)
batch_x, batch_y = dataset[0]
plt.imshow(batch_x[0])

from keras.models import Sequential, Model
from keras.layers import Input, Dense, Dropout, Activation, Flatten, Conv2D, BatchNormalization, Reshape, MaxPooling2D

def build_model(input_shape=(16, 16, 3), outputs=9):
  model = Sequential([
    Conv2D(16, 3, padding='same', activation='relu', input_shape=input_shape),
    MaxPooling2D(),
    Conv2D(32, 3, padding='same', activation='relu'),
    MaxPooling2D(),
    Conv2D(64, 3, padding='same', activation='relu'),
    MaxPooling2D(),
    Dropout(0.2),
    Flatten(),
    Dense(128, activation='relu'),
    Dense(outputs, activation='softmax')
  ])
  return model

model = build_model(input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3), outputs=9)

model.summary()

from keras.optimizers import Adam
opt = Adam(lr=LEARNING_RATE)
model.compile(loss = 'categorical_crossentropy', optimizer = opt, metrics = ['accuracy'])

dataset = DataGenerator(x_train, y_train_onehot, batch_size=32, shuffle=True, balanced=BALANCED)

best_f1 = 0.0
early_stop_counter = 0
model_save_path = os.path.join(PATH, NAME + '.h5')
history_accum = {k:[] for k in ['loss', 'accuracy', 'val_loss', 'val_accuracy', 'f1_score']}

from sklearn.metrics import f1_score

for epoch in range(EPOCHS):
  history = model.fit_generator(dataset)

  y_pred_soft = model.predict(x_valid)
  y_pred = np.array(onehot_helper.recover(y_pred_soft))
  f1 = f1_score(y_valid, y_pred, average='macro')
  print('f1:', f1)
  for k in history.history:
    history_accum[k] += history.history[k]
  history_accum['f1_score'] += [f1]
  early_stop_counter += 1
  if best_f1 < f1:
    best_f1 = f1
    early_stop_counter = 0
    print('Best f1 changed:', best_f1)
    os.makedirs(PATH, exist_ok=True)
    model.save(model_save_path)
  if early_stop_counter >= EARLY_STOPPING:
    break

model = keras.models.load_model(model_save_path)

y_pred_soft = model.predict(x_valid)
y_pred = np.array(onehot_helper.recover(y_pred_soft))

from sklearn.metrics import f1_score, recall_score, precision_score
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc

# 결과 기록
os.makedirs(PATH, exist_ok=True)
with open(os.path.join(PATH, 'result.txt'), 'w') as f:
  f1_res = f1_score(y_valid, y_pred, average='macro')
  f.write(str(f1_res))
  f.write('\n')
  print(f1_res)

  report = classification_report(y_valid, y_pred)
  print(report)
  f.write(str(report))
  f.write('\n')
  conf = confusion_matrix(y_valid, y_pred)
  print(conf)
  f.write(str(conf))
  f.write('\n')

  f.write(str(history_accum))
  f.write('\n')
  print(history_accum)

y_test_soft = model.predict(x_test)
y_test = np.array(onehot_helper.recover(y_test_soft))

pd.DataFrame({
    'failureNum': y_test
}).to_pickle(os.path.join(PATH, 'y_test_pred.pkl'))

