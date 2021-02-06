import cai.layers
import cai.util
from tensorflow import keras
#import tensorflow.keras.backend
#import tensorflow.keras.layers
#import tensorflow.keras.utils
#from tensorflow.keras.applications.imagenet_utils import _obtain_input_shape
from tensorflow.keras.models import Model
from tensorflow.keras.models import model_from_json
import numpy as np

def save_model(model, base_name):
    """Saves a model with its weights.
    # Arguments
        model: Keras model instance to be saved.
        base_name: base file name
    """
    text_file = open(base_name+'.model', "w")
    text_file.write(model.to_json())
    text_file.close()
    model.save_weights(base_name+'.h5')

def load_model(base_name):
    """Loads a model with its weights
    # Arguments
        base_name: base file name
    # Returns
        a model with its weights.
    """
    model = Model()
    text_file = open(base_name+'.model',"r")
    config = text_file.read()
    model = model_from_json(config,  {'CopyChannels': cai.layers.CopyChannels})
    model.load_weights(base_name+'.h5')
    return model

def plant_leaf(pinput_shape, num_classes,  l2_decay=0.0, dropout_drop_rate=0.2, has_batch_norm=True):
    """Implements the architecture found on the paper: 
        Identification of plant leaf diseases using a nine-layer deep convolutional neural network.
        https://www.sciencedirect.com/science/article/pii/S0045790619300023
    """
    img_input = keras.layers.Input(shape=pinput_shape)
    last_tensor = keras.layers.Conv2D(32, (3, 3), padding='valid',
        input_shape=pinput_shape, 
        kernel_regularizer=keras.regularizers.l2(l2_decay))(img_input)
    if (has_batch_norm): last_tensor = keras.layers.BatchNormalization(axis=3, epsilon=1.001e-5)(last_tensor)
    last_tensor = keras.layers.Activation('relu')(last_tensor)
    last_tensor = keras.layers.MaxPooling2D(2, strides=2)(last_tensor)
    
    last_tensor = keras.layers.Conv2D(16, (3, 3), padding='valid',
        input_shape=pinput_shape, 
        kernel_regularizer=keras.regularizers.l2(l2_decay))(last_tensor)
    if (has_batch_norm): last_tensor = keras.layers.BatchNormalization(axis=3, epsilon=1.001e-5)(last_tensor)
    last_tensor = keras.layers.Activation('relu')(last_tensor)
    last_tensor = keras.layers.MaxPooling2D(2, strides=2)(last_tensor)
    
    last_tensor = keras.layers.Conv2D(8, (3, 3), padding='valid',
        input_shape=pinput_shape, 
        kernel_regularizer=keras.regularizers.l2(l2_decay))(last_tensor)
    if (has_batch_norm): last_tensor = keras.layers.BatchNormalization(axis=3, epsilon=1.001e-5)(last_tensor)
    last_tensor = keras.layers.Activation('relu')(last_tensor)
    last_tensor = keras.layers.MaxPooling2D(2, strides=2)(last_tensor)
    
    last_tensor = keras.layers.Flatten()(last_tensor)
    
    last_tensor = keras.layers.Dense(128)(last_tensor)
    if (dropout_drop_rate > 0.0):
        last_tensor = keras.layers.Dropout(rate=dropout_drop_rate)(last_tensor)
    last_tensor = keras.layers.Activation('relu')(last_tensor)
    
    last_tensor = keras.layers.Dense(num_classes, activation='softmax', name='softmax')(last_tensor)            
    return Model(inputs = [img_input], outputs = [last_tensor])
    
def conv2d_bn(x,
              filters,
              num_row,
              num_col,
              padding='same',
              strides=(1, 1),
              name=None,
              use_bias=False,
              activation='relu'):
    """Utility function to apply conv + BN.

    # Arguments
        x: input tensor.
        filters: filters in `Conv2D`.
        num_row: height of the convolution kernel.
        num_col: width of the convolution kernel.
        padding: padding mode in `Conv2D`.
        strides: strides in `Conv2D`.
        name: name of the ops; will become `name + '_conv'`
            for the convolution and `name + '_bn'` for the
            batch norm layer.

    # Returns
        Output tensor after applying `Conv2D` and `BatchNormalization`.
    """
    if name is not None:
        bn_name = name + '_bn'
        conv_name = name + '_conv'
    else:
        bn_name = None
        conv_name = None
    if keras.backend.image_data_format() == 'channels_first':
        bn_axis = 1
    else:
        bn_axis = 3
    x = keras.layers.Conv2D(
        filters, (num_row, num_col),
        strides=strides,
        padding=padding,
        use_bias=use_bias,
        name=conv_name)(x)
    x = keras.layers.BatchNormalization(axis=bn_axis, scale=False, name=bn_name)(x)
    x = keras.layers.Activation(activation=activation, name=name)(x)
    return x

def create_inception_v3_mixed_layer(x,  id,  name='', channel_axis=3, bottleneck_compression=1,  compression=1):
    if id == 0:
            # mixed 0: 35 x 35 x 256
            branch1x1 = conv2d_bn(x, int(bottleneck_compression*64), 1, 1)
            branch5x5 = conv2d_bn(x, int(bottleneck_compression*48), 1, 1)
            branch5x5 = conv2d_bn(branch5x5, int(compression*64), 5, 5)
            branch3x3dbl = conv2d_bn(x, int(compression*64), 1, 1)
            branch3x3dbl = conv2d_bn(branch3x3dbl, int(compression*96), 3, 3)
            branch3x3dbl = conv2d_bn(branch3x3dbl, int(compression*96), 3, 3)
            branch_pool = keras.layers.AveragePooling2D((3, 3),
                                                  strides=(1, 1),
                                                  padding='same')(x)
            branch_pool = conv2d_bn(branch_pool, int(bottleneck_compression*32), 1, 1)
            x = keras.layers.concatenate([branch1x1, branch5x5, branch3x3dbl, branch_pool], axis=channel_axis, name=name)
    
    if id == 1:
        # mixed 1: 35 x 35 x 288
        branch1x1 = conv2d_bn(x, int(bottleneck_compression*64), 1, 1)
        branch5x5 = conv2d_bn(x, int(bottleneck_compression*48), 1, 1)
        branch5x5 = conv2d_bn(branch5x5, int(compression*64), 5, 5)
        branch3x3dbl = conv2d_bn(x, int(compression*64), 1, 1)
        branch3x3dbl = conv2d_bn(branch3x3dbl, int(compression*96), 3, 3)
        branch3x3dbl = conv2d_bn(branch3x3dbl, int(compression*96), 3, 3)
        branch_pool = keras.layers.AveragePooling2D((3, 3), strides=(1, 1), padding='same')(x)
        branch_pool = conv2d_bn(branch_pool, int(bottleneck_compression*64), 1, 1)
        x = keras.layers.concatenate( [branch1x1, branch5x5, branch3x3dbl, branch_pool], axis=channel_axis, name=name)

    if id == 2:
        # mixed 2: 35 x 35 x 288
        branch1x1 = conv2d_bn(x, int(bottleneck_compression*64), 1, 1)
        branch5x5 = conv2d_bn(x, int(bottleneck_compression*48), 1, 1)
        branch5x5 = conv2d_bn(branch5x5, int(compression*64), 5, 5)
        branch3x3dbl = conv2d_bn(x, int(compression*64), 1, 1)
        branch3x3dbl = conv2d_bn(branch3x3dbl, int(compression*96), 3, 3)
        branch3x3dbl = conv2d_bn(branch3x3dbl, int(compression*96), 3, 3)
        branch_pool = keras.layers.AveragePooling2D((3, 3), strides=(1, 1), padding='same')(x)
        branch_pool = conv2d_bn(branch_pool, int(bottleneck_compression*64), 1, 1)
        x = keras.layers.concatenate( [branch1x1, branch5x5, branch3x3dbl, branch_pool], axis=channel_axis, name=name)

    if id == 3:
        # mixed 3: 17 x 17 x 768
        branch3x3 = conv2d_bn(x, int(bottleneck_compression*384), 3, 3, strides=(2, 2), padding='valid')
        branch3x3dbl = conv2d_bn(x, int(bottleneck_compression*64), 1, 1)
        branch3x3dbl = conv2d_bn(branch3x3dbl, int(compression*96), 3, 3)
        branch3x3dbl = conv2d_bn(branch3x3dbl, int(compression*96), 3, 3, strides=(2, 2), padding='valid')
        branch_pool = keras.layers.MaxPooling2D((3, 3), strides=(2, 2))(x)
        x = keras.layers.concatenate( [branch3x3, branch3x3dbl, branch_pool], axis=channel_axis, name=name)

    if id == 4:
        # mixed 4: 17 x 17 x 768
        branch1x1 = conv2d_bn(x, int(bottleneck_compression*192), 1, 1)
        branch7x7 = conv2d_bn(x, int(bottleneck_compression*128), 1, 1)
        branch7x7 = conv2d_bn(branch7x7, int(compression*128), 1, 7)
        branch7x7 = conv2d_bn(branch7x7, int(compression*192), 7, 1)
        branch7x7dbl = conv2d_bn(x, int(bottleneck_compression*128), 1, 1)
        branch7x7dbl = conv2d_bn(branch7x7dbl, int(compression*128), 7, 1)
        branch7x7dbl = conv2d_bn(branch7x7dbl, int(compression*128), 1, 7)
        branch7x7dbl = conv2d_bn(branch7x7dbl, int(compression*128), 7, 1)
        branch7x7dbl = conv2d_bn(branch7x7dbl, int(compression*192), 1, 7)
        branch_pool = keras.layers.AveragePooling2D((3, 3), strides=(1, 1), padding='same')(x)
        branch_pool = conv2d_bn(branch_pool, int(bottleneck_compression*192), 1, 1)
        x = keras.layers.concatenate([branch1x1, branch7x7, branch7x7dbl, branch_pool], axis=channel_axis, name=name)

    if ((id == 5) or (id == 6)):
        branch1x1 = conv2d_bn(x, int(bottleneck_compression*192), 1, 1)
        branch7x7 = conv2d_bn(x, int(bottleneck_compression*160), 1, 1)
        branch7x7 = conv2d_bn(branch7x7, int(compression*160), 1, 7)
        branch7x7 = conv2d_bn(branch7x7, int(compression*192), 7, 1)
        branch7x7dbl = conv2d_bn(x, int(bottleneck_compression*160), 1, 1)
        branch7x7dbl = conv2d_bn(branch7x7dbl, int(compression*160), 7, 1)
        branch7x7dbl = conv2d_bn(branch7x7dbl, int(compression*160), 1, 7)
        branch7x7dbl = conv2d_bn(branch7x7dbl, int(compression*160), 7, 1)
        branch7x7dbl = conv2d_bn(branch7x7dbl, int(compression*192), 1, 7)
        branch_pool = keras.layers.AveragePooling2D( (3, 3), strides=(1, 1), padding='same')(x)
        branch_pool = conv2d_bn(branch_pool, int(bottleneck_compression*192), 1, 1)
        x = keras.layers.concatenate([branch1x1, branch7x7, branch7x7dbl, branch_pool], axis=channel_axis, name=name)

    if id == 7:
        # mixed 7: 17 x 17 x 768
        branch1x1 = conv2d_bn(x, int(bottleneck_compression*192), 1, 1)
        branch7x7 = conv2d_bn(x, int(bottleneck_compression*192), 1, 1)
        branch7x7 = conv2d_bn(branch7x7, int(compression*192), 1, 7)
        branch7x7 = conv2d_bn(branch7x7, int(compression*192), 7, 1)
        branch7x7dbl = conv2d_bn(x, int(compression*192), 1, 1)
        branch7x7dbl = conv2d_bn(branch7x7dbl, int(compression*192), 7, 1)
        branch7x7dbl = conv2d_bn(branch7x7dbl, int(compression*192), 1, 7)
        branch7x7dbl = conv2d_bn(branch7x7dbl, int(compression*192), 7, 1)
        branch7x7dbl = conv2d_bn(branch7x7dbl, int(compression*192), 1, 7)
        branch_pool = keras.layers.AveragePooling2D((3, 3), strides=(1, 1), padding='same')(x)
        branch_pool = conv2d_bn(branch_pool, int(bottleneck_compression*192), 1, 1)
        x = keras.layers.concatenate([branch1x1, branch7x7, branch7x7dbl, branch_pool], axis=channel_axis, name=name)

    if id == 8:
        # mixed 8: 8 x 8 x 1280
        branch3x3 = conv2d_bn(x, int(bottleneck_compression*192), 1, 1)
        branch3x3 = conv2d_bn(branch3x3, int(compression*320), 3, 3, strides=(2, 2), padding='valid')
        branch7x7x3 = conv2d_bn(x, int(bottleneck_compression*192), 1, 1)
        branch7x7x3 = conv2d_bn(branch7x7x3, int(compression*192), 1, 7)
        branch7x7x3 = conv2d_bn(branch7x7x3, int(compression*192), 7, 1)
        branch7x7x3 = conv2d_bn(branch7x7x3, int(compression*192), 3, 3, strides=(2, 2), padding='valid')
        branch_pool = keras.layers.MaxPooling2D((3, 3), strides=(2, 2))(x)
        x = keras.layers.concatenate([branch3x3, branch7x7x3, branch_pool], axis=channel_axis, name=name)

    if (id == 9) or (id==10):
        # mixed 9: 8 x 8 x 2048
        branch1x1 = conv2d_bn(x, int(bottleneck_compression*320), 1, 1)
        branch3x3 = conv2d_bn(x, int(bottleneck_compression*384), 1, 1)
        branch3x3_1 = conv2d_bn(branch3x3, int(compression*384), 1, 3)
        branch3x3_2 = conv2d_bn(branch3x3, int(compression*384), 3, 1)
        branch3x3 = keras.layers.concatenate([branch3x3_1, branch3x3_2], axis=channel_axis, name=name + 'a')
        branch3x3dbl = conv2d_bn(x, int(bottleneck_compression*448), 1, 1)
        branch3x3dbl = conv2d_bn(branch3x3dbl, int(compression*384), 3, 3)
        branch3x3dbl_1 = conv2d_bn(branch3x3dbl, int(compression*384), 1, 3)
        branch3x3dbl_2 = conv2d_bn(branch3x3dbl, int(compression*384), 3, 1)
        branch3x3dbl = keras.layers.concatenate([branch3x3dbl_1, branch3x3dbl_2], axis=channel_axis)
        branch_pool = keras.layers.AveragePooling2D((3, 3), strides=(1, 1), padding='same')(x)
        branch_pool = conv2d_bn(branch_pool, int(bottleneck_compression*192), 1, 1)
        x = keras.layers.concatenate([branch1x1, branch3x3, branch3x3dbl, branch_pool], axis=channel_axis, name=name + 'b')
    return x

def create_inception_path(last_tensor,  compression=0.5,  channel_axis=3,  name=None):
    channel_count = int(keras.backend.int_shape(last_tensor)[channel_axis] * compression)
    return conv2d_bn(last_tensor, channel_count, 1, 1,  name=name)
    
def create_inception_v3_two_path_mixed_layer(x,  id,  name='',  channel_axis=3,  bottleneck_compression=0.5,  compression=0.655):
    if name=='':
        name='mixed'
    a = create_inception_v3_mixed_layer(x,  id=id,  name=name+'a', bottleneck_compression=bottleneck_compression, compression=compression)
    b = create_inception_v3_mixed_layer(x,  id=id,  name=name+'b', bottleneck_compression=bottleneck_compression, compression=compression)
    return keras.layers.Concatenate(axis=channel_axis, name=name)([a, b])

def two_path_inception_v3(
                include_top=True,
                weights=None, #'two_paths_plant_leafs'
                input_shape=(224,224,3),
                pooling=None,
                classes=1000,
                two_paths_partial_first_block=0,
                two_paths_first_block=False,
                two_paths_second_block=False,
                deep_two_paths=False,
                deep_two_paths_compression=0.655,
                deep_two_paths_bottleneck_compression=0.5,
                l_ratio=0.5,
                ab_ratio=0.5,
                max_mix_idx=10, 
                model_name='two_path_inception_v3', 
                **kwargs):
    """Instantiates the Inception v3 architecture with 2 paths options.
    # Arguments
        include_top: whether to include the fully-connected
            layer at the top of the network.
        weights: one of `None` (random initialization),
              'imagenet' (pre-training on ImageNet),
              or the path to the weights file to be loaded.
        input_shape: mandatory input shape. Common values are 
            (299, 299, 3) and (224, 224, 3).
        pooling: Optional pooling mode for feature extraction
            when `include_top` is `False`.
            - `None` means that the output of the model will be
                the 4D tensor output of the
                last convolutional block.
            - `avg` means that global average pooling
                will be applied to the output of the
                last convolutional block, and thus
                the output of the model will be a 2D tensor.
            - `max` means that global max pooling will
                be applied.
        classes: optional number of classes to classify images
            into, only to be specified if `include_top` is True, and
            if no `weights` argument is specified.
        two_paths_partial_first_block: valid values are 1, 2 and 3. 1 means
            only one two-paths convolution. 2 means 2 two-paths convolutions. 3 means
            a full first two-path block. Other values mean nothing.
        two_paths_first_block: when true, starts with 2 paths for 
            the first 3 convolutions.
        two_paths_second_block: when true, another 2 convolutions
            are done in two paths.
        deep_two_paths: when true, creates a complete two-path architecture.
        deep_two_paths_compression: how much each path should be compressed.
        l_ratio: proportion dedicated to light.
        ab_ratio: proportion dedicated to color.
        max_mix_idx: last "mixed layer" index. You can create smaller
            architectures with this parameter.
        model_name: model name 
    # Returns
        A Keras model instance.
    # Raises
        ValueError: in case of invalid argument for `weights`,
            or invalid input shape.
    """
    img_input = keras.layers.Input(shape=input_shape)

    if keras.backend.image_data_format() == 'channels_first':
        channel_axis = 1
    else:
        channel_axis = 3
    
    if two_paths_partial_first_block==3:
        two_paths_partial_first_block=0
        two_paths_first_block=True
        two_paths_second_block=False

    if two_paths_partial_first_block>3:
        two_paths_partial_first_block=0
        two_paths_first_block=True
        two_paths_second_block=True

    if (two_paths_second_block):
        two_paths_first_block=True
    
    include_first_block=True
    if (two_paths_partial_first_block==1) or (two_paths_partial_first_block==2):
        two_paths_second_block=False
        two_paths_first_block=False
        include_first_block=False

        # Only 1 convolution with two-paths?
        if (two_paths_partial_first_block==1):
            l_branch = cai.layers.CopyChannels(0,1)(img_input)
            l_branch = conv2d_bn(l_branch, int(round(32*l_ratio)), 3, 3, strides=(2, 2), padding='valid')

            ab_branch = cai.layers.CopyChannels(1,2)(img_input)
            ab_branch = conv2d_bn(ab_branch, int(round(32*ab_ratio)), 3, 3, strides=(2, 2), padding='valid')

            single_branch  = keras.layers.Concatenate(axis=channel_axis, name='concat_partial_first_block1')([l_branch, ab_branch])
            single_branch = conv2d_bn(single_branch, 32, 3, 3, padding='valid')
            single_branch = conv2d_bn(single_branch, 64, 3, 3)
            x = keras.layers.MaxPooling2D((3, 3), strides=(2, 2))(single_branch)

        # Only 2 convolution with two-paths?
        if (two_paths_partial_first_block==2):
            l_branch = cai.layers.CopyChannels(0,1)(img_input)
            l_branch = conv2d_bn(l_branch, int(round(32*l_ratio)), 3, 3, strides=(2, 2), padding='valid')
            l_branch = conv2d_bn(l_branch, int(round(32*l_ratio)), 3, 3, padding='valid')

            ab_branch = cai.layers.CopyChannels(1,2)(img_input)
            ab_branch = conv2d_bn(ab_branch, int(round(32*ab_ratio)), 3, 3, strides=(2, 2), padding='valid')
            ab_branch = conv2d_bn(ab_branch, int(round(32*ab_ratio)), 3, 3, padding='valid')

            single_branch = keras.layers.Concatenate(axis=channel_axis, name='concat_partial_first_block2')([l_branch, ab_branch])
            single_branch = conv2d_bn(single_branch, 64, 3, 3)
            x = keras.layers.MaxPooling2D((3, 3), strides=(2, 2))(single_branch)

    if include_first_block:
        if two_paths_first_block:
            l_branch = cai.layers.CopyChannels(0,1)(img_input)
            l_branch = conv2d_bn(l_branch, int(round(32*l_ratio)), 3, 3, strides=(2, 2), padding='valid')
            l_branch = conv2d_bn(l_branch, int(round(32*l_ratio)), 3, 3, padding='valid')
            l_branch = conv2d_bn(l_branch, int(round(64*l_ratio)), 3, 3)
            l_branch = keras.layers.MaxPooling2D((3, 3), strides=(2, 2))(l_branch)

            ab_branch = cai.layers.CopyChannels(1,2)(img_input)
            ab_branch = conv2d_bn(ab_branch, int(round(32*ab_ratio)), 3, 3, strides=(2, 2), padding='valid')
            ab_branch = conv2d_bn(ab_branch, int(round(32*ab_ratio)), 3, 3, padding='valid')
            ab_branch = conv2d_bn(ab_branch, int(round(64*ab_ratio)), 3, 3)
            ab_branch = keras.layers.MaxPooling2D((3, 3), strides=(2, 2))(ab_branch)
            x = keras.layers.Concatenate(axis=channel_axis, name='concat_first_block')([l_branch, ab_branch])
        else:
            single_branch = conv2d_bn(img_input, 32, 3, 3, strides=(2, 2), padding='valid')
            single_branch = conv2d_bn(single_branch, 32, 3, 3, padding='valid')
            single_branch = conv2d_bn(single_branch, 64, 3, 3)
            single_branch = keras.layers.MaxPooling2D((3, 3), strides=(2, 2))(single_branch)
            # print('single path first block')
            x = single_branch

    if (two_paths_second_block):
      l_branch = conv2d_bn(x, int(round(80*deep_two_paths_compression)), 1, 1, padding='valid')
      l_branch = conv2d_bn(l_branch, int(round(192*deep_two_paths_compression)), 3, 3, padding='valid')
      ab_branch = conv2d_bn(x, int(round(80*deep_two_paths_compression)), 1, 1, padding='valid')
      ab_branch = conv2d_bn(ab_branch, int(round(192*deep_two_paths_compression)), 3, 3, padding='valid')
      x = keras.layers.Concatenate(axis=channel_axis, name='concat_second_block')([l_branch, ab_branch])
      x = keras.layers.MaxPooling2D((3, 3), strides=(2, 2))(x)
    else:
      x = conv2d_bn(x, 80, 1, 1, padding='valid')
      x = conv2d_bn(x, 192, 3, 3, padding='valid')
      x = keras.layers.MaxPooling2D((3, 3), strides=(2, 2))(x)
      # print('single path second block')

    if max_mix_idx >= 0:
        for id_layer in range(max_mix_idx+1):
            if (deep_two_paths):
                x = create_inception_v3_two_path_mixed_layer(x,  id=id_layer,  name='mixed'+str(id_layer), channel_axis=channel_axis, bottleneck_compression=deep_two_paths_bottleneck_compression, compression=deep_two_paths_compression)
            else:
                x = create_inception_v3_mixed_layer(x,  id=id_layer,  name='mixed'+str(id_layer), channel_axis=channel_axis)
    
    if include_top:
        # Classification block
        x = keras.layers.GlobalAveragePooling2D(name='avg_pool')(x)
        x = keras.layers.Dense(classes, activation='softmax', name='predictions')(x)
    else:
        if pooling == 'avg':
            x = keras.layers.GlobalAveragePooling2D()(x)
        elif pooling == 'max':
            x = keras.layers.GlobalMaxPooling2D()(x)

    inputs = img_input
    # Create model.
    model = keras.models.Model(inputs, x, name=model_name)
    return model

def create_paths(last_tensor, compression, l2_decay, dropout_rate=0.0):
    """Builds a new path from a previous main branch.
    # Arguments
        last_tensor: input tensor.
        compression: float, compression rate at transition layers.
        l2_decay: float.
        dropout_rate: if bigger than zero, adds a dropout layer.
    # Returns
        output tensor for the block.
    """
    bn_axis = 3
    last_tensor = keras.layers.Conv2D(int(keras.backend.int_shape(last_tensor)[bn_axis] * compression), 1,
                      use_bias=True, activation='relu',
                      kernel_regularizer=keras.regularizers.l2(l2_decay))(last_tensor)
    if (dropout_rate>0): last_tensor = keras.layers.Dropout(dropout_rate)(last_tensor)
    last_tensor = keras.layers.MaxPooling2D(2, strides=2)(last_tensor)
    return last_tensor

def compiled_full_two_path_inception_v3(
    input_shape=(224,224,3),
    classes=1000,
    max_mix_idx=10, 
    model_name='two_path_inception_v3'):
    """Returns a compiled full two-paths inception v3.
    # Arguments
        input_shape: mandatory input shape. Common values are 
            (299, 299, 3) and (224, 224, 3).
        classes: number of classes to classify images into.
        max_mix_idx: last "mixed layer" index. You can create smaller
            architectures with this parameter.
        model_name: model name 
    # Returns
        A Keras model instance.
    # Raises
        ValueError: in case of invalid argument for `weights`,
            or invalid input shape.
    """
    return compiled_two_path_inception_v3(
        input_shape=input_shape,
        classes=classes,
        two_paths_partial_first_block=0,
        two_paths_first_block=True,
        two_paths_second_block=True,
        deep_two_paths=True,
        deep_two_paths_compression=0.57,
        max_mix_idx=max_mix_idx, 
        model_name='deep_two_path_inception_v3'
    )
    
def compiled_inception_v3(
    input_shape=(224,224,3),
    classes=1000,
    max_mix_idx=10, 
    model_name='two_path_inception_v3'):
    """Returns a compiled two-paths inception v3.
    # Arguments
        input_shape: mandatory input shape. Common values are 
            (299, 299, 3) and (224, 224, 3).
        classes: number of classes to classify images into.
        max_mix_idx: last "mixed layer" index. You can create smaller
            architectures with this parameter.
        model_name: model name 
    # Returns
        A Keras model instance.
    # Raises
        ValueError: in case of invalid argument for `weights`,
            or invalid input shape.
    """
    return compiled_two_path_inception_v3(
        input_shape=input_shape,
        classes=classes,
        two_paths_partial_first_block=0,
        two_paths_first_block=False,
        two_paths_second_block=False,
        deep_two_paths=False,
        max_mix_idx=max_mix_idx, 
        model_name='two_path_inception_v3'
    )

def compiled_two_path_inception_v3(
    input_shape=(224,224,3),
    classes=1000,
    two_paths_partial_first_block=0,
    two_paths_first_block=False,
    two_paths_second_block=False,
    deep_two_paths=False,
    deep_two_paths_compression=0.655,
    deep_two_paths_bottleneck_compression=0.5,
    l_ratio=0.5,
    ab_ratio=0.5,
    max_mix_idx=10, 
    model_name='two_path_inception_v3'
    ):
    """Returns a compiled two-paths inception v3.
    # Arguments
        input_shape: mandatory input shape. Common values are 
            (299, 299, 3) and (224, 224, 3).
        classes: number of classes to classify images into.
        two_paths_partial_first_block: valid values are 1, 2 and 3. 1 means
            only one two-paths convolution. 2 means 2 two-paths convolutions. 3 means
            a full first two-path block. Other values mean nothing.
        two_paths_first_block: when true, starts with 2 paths for 
            the first 3 convolutions.
        two_paths_second_block: when true, another 2 convolutions
            are done in two paths.
        deep_two_paths: when true, creates a complete two-path architecture.
        deep_two_paths_compression: how much each path should be compressed.
        l_ratio: proportion dedicated to light.
        ab_ratio: proportion dedicated to color.
        max_mix_idx: last "mixed layer" index. You can create smaller
            architectures with this parameter.
        model_name: model name 
    # Returns
        A Keras model instance.
    # Raises
        ValueError: in case of invalid argument for `weights`,
            or invalid input shape.
    """
    base_model = cai.models.two_path_inception_v3(
        include_top=False, # Has to be false to be compiled below.
        weights=None,
        input_shape=input_shape,
        pooling=None, # Has to be none to be compiled below.
        classes=classes,
        two_paths_partial_first_block=two_paths_partial_first_block,
        two_paths_first_block=two_paths_first_block,
        two_paths_second_block=two_paths_second_block,
        deep_two_paths=deep_two_paths,
        deep_two_paths_compression=deep_two_paths_compression,
        deep_two_paths_bottleneck_compression=deep_two_paths_bottleneck_compression,
        l_ratio=l_ratio,
        ab_ratio=ab_ratio,
        max_mix_idx=max_mix_idx, 
        model_name=model_name
    )
    x = base_model.output
    x = keras.layers.GlobalAveragePooling2D()(x)
    x = keras.layers.Dense(classes, name='preprediction')(x)
    predictions = keras.layers.Activation('softmax',name='prediction')(x)
    model = Model(inputs=base_model.input, outputs=predictions)
    model.compile(loss='categorical_crossentropy',
    optimizer="sgd",
    metrics=['accuracy','top_k_categorical_accuracy'])
    return model

def CreatePartialModel(pModel, pOutputLayerName, hasGlobalAvg=False):
  """Creates a partial model up to the layer name defined in pOutputLayerName.
  # Arguments
    pModel: original model.
    pOutputLayerName: last layer in the partial model.
    hasGlobalAvg: when True, adds a global average pooling at the end.
  """
  inputs = pModel.input
  outputs = pModel.get_layer(pOutputLayerName).output
  if (hasGlobalAvg):
    outputs = keras.layers.GlobalAveragePooling2D()(outputs)
  return keras.Model(inputs=inputs, outputs=outputs)

def CreatePartialModelCopyingChannels(pModel, pOutputLayerName, pChannelStart, pChannelCount):
  """Creates a partial model up to the layer name defined in pOutputLayerName and then copies channels starting from pChannelStart with pChannelCount channels.
  # Arguments
    pModel: original model.
    pOutputLayerName: last layer in the partial model.
    hasGlobalAvg: when True, adds a global average pooling at the end.
    pChannelStart: first channel to be loaded.
    pChannelCount: channels to be loaded.    
  """
  inputs = pModel.input
  outputs = pModel.get_layer(pOutputLayerName).output
  outputs = cai.layers.CopyChannels(channel_start=pChannelStart, channel_count=pChannelCount)(outputs)
  return keras.Model(inputs=inputs, outputs=outputs)

def PartialModelPredict(aInput, pModel, pOutputLayerName, hasGlobalAvg=False, pBatchSize=32):
  """Creates a partial model up to the layer name defined in pOutputLayerName and run it
  with aInput.  
  # Arguments
    aInput: array with Input elements.
    pModel: original model.
    pOutputLayerName: last layer in the partial model.
    hasGlobalAvg: when True, adds a global average pooling at the end. 
  """  
  inputs = pModel.input
  outputs = pModel.get_layer(pOutputLayerName).output
  if (hasGlobalAvg):
    outputs = keras.layers.GlobalAveragePooling2D()(outputs)
  IntermediateLayerModel = keras.Model(inputs=inputs, outputs=outputs)
  layeroutput = np.array(IntermediateLayerModel.predict(x=aInput, batch_size=pBatchSize))
  IntermediateLayerModel = 0
  return layeroutput

def calculate_heat_map_from_dense_and_avgpool(aInput, target_class, pModel, pOutputLayerName, pDenseLayerName):
  """Creates a heatmap from a model that has a global avg pool followed by a dense layer.  
  # Arguments
    aInput: array with Input elements.
    pModel: original model.
    pOutputLayerName: last layer before the global avg pool.
    pDenseLayerName: dense layer found probably before a softmax.
  """
  localImageArray = []
  localImageArray.append(aInput)
  localImageArray = np.array(localImageArray)
  class_weights = pModel.get_layer(pDenseLayerName).get_weights()[0]
  conv_output = cai.models.PartialModelPredict(localImageArray, pModel, pOutputLayerName)[0]
  a_heatmap_result = np.zeros(dtype = np.float32, shape = conv_output.shape[0:2])
  #print(a_heatmap_result.shape)
  #print(type(conv_output[:, :, 0]))
  #print(conv_output[:, :, 0].shape)
  for i, w in enumerate(class_weights[:, target_class]):
    a_heatmap_result += w * conv_output[:, :, i]
  a_heatmap_result = cai.util.relu(a_heatmap_result)
  max_heatmap_result = np.max(a_heatmap_result)
  if max_heatmap_result > 0:
      a_heatmap_result = a_heatmap_result / max_heatmap_result 
  return a_heatmap_result
