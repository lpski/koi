from typing import NamedTuple, List, Optional



class Conv2dConfig(object):
    filters: int = 30
    kernel_size: int = 2
    stride: int = 1
    regularizer: float = 0.0
    dropout: float = 0
    pool_size: int = 2
    normalize_index: int = None
    padding: str = 'valid'

    def __init__(self, filters: int = 30, kernel_size: int = 2, stride: int = 1, regularizer: float = 0, dropout: float = 0, pool_size: int = 0, normalize_index: Optional[int] = None, padding: str = 'valid'):
        self.filters = filters
        self.stride = stride
        self.regularizer = regularizer
        self.dropout = dropout
        self.pool_size = pool_size
        self.normalize_index = normalize_index
        self.padding = padding
        if isinstance(kernel_size, list): self.kernel_size = tuple(kernel_size)
        else: self.kernel_size = kernel_size

    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)


class DenseConfig(object):
    units: int = 1
    dropout: float = 0

    def __init__(self, units: int = 1, dropout: float = 0):
        self.units = units
        self.dropout = dropout

    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)

class ModelParams(object):
    cnn_layers: List[Conv2dConfig]
    dense_layers: List[DenseConfig]

    upsample: Optional[tuple]
    batch_size: int
    epochs: int
    optimizer: str
    lr: float
    lookback: int
    n_feats: int
    flush_models: bool


    def __init__(self, cnn_layers: List[Conv2dConfig] = None, dense_layers: List[DenseConfig] = None, optimizer: str = 'adam', lr: float = 0.001, epochs: int = 200, batch_size: int = 20, lookback: int = 3, n_feats: int = 225, flush_models: bool = True, upsample: Optional[tuple] = None):
        if cnn_layers is None: self.cnn_layers = []
        else: self.cnn_layers = cnn_layers

        if dense_layers is None: self.dense_layers = []
        else: self.dense_layers = dense_layers

        if isinstance(upsample, list): self.upsample = tuple(upsample)
        else: self.upsample = upsample

        self.optimizer = optimizer
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.lookback = lookback
        self.n_feats = n_feats
        self.flush_models = flush_models

    
    @classmethod
    def from_json(cls, data: dict):
        # Format layer arrays
        cnns = []
        if 'cnn_layers' in data:
            cnns = list(map(lambda c: Conv2dConfig.from_json(c), data['cnn_layers']))
            del data['cnn_layers']
        
        dense = []
        if 'dense_layers' in data:
            dense = list(map(lambda c: DenseConfig.from_json(c), data['dense_layers']))
            del data['dense_layers']


        return cls(**data, cnn_layers=cnns, dense_layers=dense)



