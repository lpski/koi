from ib_insync.contract import Contract
import numpy as np, os, pandas as pd, math, json, random, tensorflow as tf
from typing import Dict, List, Optional, Tuple, Union
from tensorflow.keras.models import load_model, Sequential, Model
from tensorflow.keras.layers import Conv2D, MaxPool2D, BatchNormalization, Dropout, Flatten, Dense, UpSampling2D
from tensorflow.keras import regularizers, optimizers, backend as K
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from sklearn.preprocessing import MinMaxScaler, RobustScaler
from sklearn.utils import compute_class_weight
from uuid import uuid4
from pickle import load, dump
from koi.modeling.modeling_models import ModelParams
from koi.models import CryptoContract, Prediction, Direction

###########
# Helpers
###########

def create_model(params: ModelParams, input_shape: Tuple) -> Tuple[Model, List]:
    """Given a set of params, returns a compiled CNN model"""
    model = Sequential()

    # Conv Layers


    # FC Layers

    # Output Layer
    model.add(Dense(3, activation='softmax'))


    # Compiling + Summary
    if params.optimizer == 'rmsprop': optimizer = optimizers.RMSprop(lr=params.lr)
    elif params.optimizer == 'sgd': optimizer = optimizers.SGD(lr=params.lr, decay=1e-6, momentum=0.9, nesterov=True)
    elif params.optimizer == 'adam': optimizer = optimizers.Adam(learning_rate=params.lr, beta_1=0.9, beta_2=0.999, amsgrad=False)
    else: raise Exception('Invalid Optimizer')
    model.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics=['accuracy'], sample_weight_mode='temporal')

    # Generate interim ID
    model_id = str(uuid4())
    model_path = f'config/temp_models/{model_id}'
    if not os.path.exists(model_path): os.mkdir(model_path)

    # Generate Helpers
    callbacks = [
        # ...
        ModelCheckpoint(model_path, monitor='val_loss', verbose=0, save_best_only=True, save_weights_only=False, mode='min', period=1)
    ]
    return (model, callbacks)


def reshape_as_image(X: np.ndarray, width: int, height: int):
    x_temp = np.zeros((X.shape[0], width, height))
    for im_index in range(X.shape[0]):
        for i in range(width*height):
            row, col = i // height, i % width
            x_temp[im_index][row][col] = X[im_index][i]

    return x_temp


def reshape_for_batch_size(train_X: np.ndarray, train_y: np.ndarray = None, test_X: np.ndarray = None, test_y: np.ndarray = None, batch_size: int = 100):
    """Reshape data to ensure length % batch size == 0"""

    if train_y is None: # Prediction Scenario
        train_reshape = train_X.shape[0]
        for i in range(train_X.shape[0], 1, -1):
            if i % batch_size == 0:
                train_reshape = i
                break

        return train_X[:train_reshape]
    
    else: # Train Scenario
        train_reshape, test_reshape = train_X.shape[0], test_X.shape[0]
        for i in range(train_X.shape[0], 1, -1):
            if i % batch_size == 0:
                train_reshape = i
                break
        btr_X, btr_y = train_X[:train_reshape], train_y[:train_reshape]

        for j in range(test_X.shape[0], 1, -1):
            if j % batch_size == 0:
                test_reshape = j
                break
        bte_X, bte_y = test_X[:test_reshape], test_y[:test_reshape]

        return (btr_X, btr_y, bte_X, bte_y)


def add_channel_data(X: np.ndarray) -> Tuple[np.ndarray, Tuple, int]:
    """
    Adds channel dimension at correct axis in X
    Returns: (X, input shape, channel axis)
    """
    # Add channel dimension to X
    chan_dim = -1
    if K.image_data_format=='channels_first':
        print('\n\n_____________\n\nWARNING: channels_first format required\n\n_____________\n\n')
        btr_X: np.ndarray = X.reshape(X.shape[0], 1, X.shape[1], X.shape[2])
        input_shape = (1, btr_X.shape[2], btr_X.shape[3])
        chan_dim = 1
    else:
        btr_X: np.ndarray = X.reshape(X.shape[0], X.shape[1], X.shape[2], 1)
        input_shape = (btr_X.shape[1], btr_X.shape[2], 1)

    return (btr_X, input_shape, chan_dim)



def prepare_data(df: pd.DataFrame, symbol: str, batch_size: int, n_feats: int = 81) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[str]]:
    """
    Returns: (X, labels, model_columns)
    """

    # Filter columns
    labels = df['labels'].values.astype(np.int)

    # Ensure dimensions are a valid square
    df_vals = df.values
    img_dim = math.floor(math.sqrt(df_vals.shape[1]))
    if img_dim**2 < df_vals.shape[1]:
        drop_count = df_vals.shape[1] - img_dim**2
        df_vals = df_vals[:, :-drop_count]

    # Split Train/Test Sets
    test_size = 2 * batch_size
    train_X, test_X = df_vals[:-test_size], df_vals[-test_size:]
    train_y, test_y = labels[:-test_size], labels[-test_size:]

    # Scale Data
    scaler = RobustScaler(with_centering=False, with_scaling=True)
    train_X: np.ndarray = scaler.fit_transform(df_vals)
    test_X: np.ndarray = scaler.transform(df_vals)

    # Reshape scaled data into image format
    train_X = reshape_as_image(train_X, img_dim, img_dim)
    test_X = reshape_as_image(test_X, img_dim, img_dim)
    
    print(f'{symbol} Data Formatting Complete')
    train_X, train_y, test_X, test_y = reshape_for_batch_size(train_X, train_y, test_X, test_y, batch_size)
    return (scaler, train_X, train_y, test_X, test_y, df.columns.tolist())


def prepare_predict_data(df: pd.DataFrame, columns: List[str], scaler: MinMaxScaler) -> np.ndarray:
    """
    Returns: X - additional modification required to fit your needs
    """
    # Filter columns
    X: np.ndarray = scaler.transform(df.values)
    X = reshape_as_image(X, 15, 15)
    return X



# Primary Class
class CNN_Manager(object):
    models: Dict[str, Tuple[Model, List[str], MinMaxScaler, int, int]] # Dict[sym, (model, cols, scaler, batch_size, lookback)]
    conf_threshold: Dict[str, float]
    config: ModelParams
    backtest: bool

    def __init__(self, symbols: List[str] = None, config: ModelParams = None, is_backtest: bool = False):
        self.models = {}
        self.conf_threshold = {}
        self.config = config
        self.backtest = is_backtest

    def load_existing_models(self, symbols: List[str]):
        for symbol in [s for s in symbols if s not in self.models]:
            filepath = f'config/models/{symbol}'
            if os.path.exists(filepath):
                # print(f'print loading {symbol} model data from {filepath}')
                # with open(f'{filepath}{"_bt" if self.backtest else ""}/config.json', 'r') as f:
                with open(f'{filepath}/config.json', 'r') as f:
                    try:
                        data = json.loads(f.read())
                        cols, conf = data['columns'], data['conf']
                        batch_size, lookback = data['model']['batch_size'], data['config']['lookback']
                    except: raise Exception(f'Unable To Load Required {symbol} Columns')

                with open(f'{filepath}/scaler.pkl', 'rb') as sf:
                    try: scaler: MinMaxScaler = load(sf)
                    except: raise Exception(f'Unable To Load Required {symbol} Scaler')

                self.models[symbol] = (load_model(filepath), cols, scaler, batch_size, lookback)
                self.conf_threshold[symbol] = conf
                print(f'{symbol} model+cols+scaler loaded')
                # self.models[symbol][0].summary()
        

    def train(self, df: pd.DataFrame, symbol: str):
        """
        Given a dataframe
            -   formats data into required CNN image format
            -   constructs & fits a model
        """
        # if symbol in self.models: return
        filepath = f'config/models/{symbol}'
        if os.path.exists(filepath):
            print(f'print loading {symbol} model data from {filepath}')
            with open(f'{filepath}/config.json', 'r') as f:
                try:
                    data = json.loads(f.read())
                    cols, conf, batch_size = data['columns'], data['conf'], data['model']['batch_size']
                except: raise Exception(f'Unable To Load Required {symbol} Columns')

            with open(f'{filepath}/scaler.pkl', 'rb') as sf:
                try: scaler: MinMaxScaler = load(sf)
                except: raise Exception(f'Unable To Load Required {symbol} Scaler')

            self.models[symbol] = (load_model(filepath), cols, scaler, batch_size, self.config.lookback)
            print(f'{symbol} model loaded')
            return

        # Label + Structure Data
        # ...
        scaler = MinMaxScaler()

        # Create + Fit Model
        input_shape = ()
        model, callbacks = create_model(self.config, input_shape)
        print(f'{symbol} Model Created:')
        model.summary()

        # model.fit(...)

        # Save models + required info
        self.models[symbol] = (model, [], scaler, self.config.batch_size, self.config.lookback)
        model.save(f'config/models/{symbol}{"_bt" if self.backtest else ""}')
        return


    def predict(self, df: pd.DataFrame, symbol: str, is_backtest: bool = False) -> Prediction:
        if symbol not in self.models:
            print(f'\n\nPOTENTIAL ERROR: {symbol} model does not exist\n\n')
            return Prediction('cnn', Direction.Unsure, 0, 'cnn prediction')

        # Implement predict logic here
        return Prediction('cnn', Direction.Unsure, 0, 'cnn prediction')



    def evaluate(self, df: pd.DataFrame, symbol: str):
        if symbol not in self.models: raise Exception(f'{symbol} not in models - can\'t evaluate')

        print(f'cnn:evaluate:{symbol}')
        model, columns, scaler, batch_size, _ = self.models[symbol]

        # Evaluate your model here: model.evaluate(...)



    # Utils
    def cols_for(self, symbol: str) -> Optional[List[str]]:
        return None

    def cols(self, contracts: List[Union[CryptoContract, Contract]]) -> Dict[str, List[str]]:
        return {}

    def lookbacks(self, symbols: List[str]) -> Dict[str, int]:
        return { sym: self.models[sym][4] if sym in self.models else self.config.lookback for sym in symbols }

