import numpy as np
import tensorflow as tf
import CIFARHelper as CIFARHelper

CIFARPath = 'cifar-10-batches-py/'

dirs = ['batches.meta', 'data_batch_1', 'data_batch_2', 'data_batch_3', 'data_batch_4', 'data_batch_5', 'test_batch']

inputs = [0, 1, 2, 3, 4, 5, 6]

for i, dir in zip(inputs, dirs):
    inputs[i] = CIFARHelper.unpickle(CIFARPath + dir)

batchMeta = inputs[0]
batch1 = inputs[1]
batch2 = inputs[2]
batch3 = inputs[3]
batch4 = inputs[4]
batch5 = inputs[5]
testBatch = inputs[6]

ch = CIFARHelper.CifarHelper(batch1=batch1,batch2=batch2,batch3=batch3,batch4=batch4,batch5=batch5,testBatch=testBatch)
ch.set_up_images()


x = tf.placeholder(tf.float32, shape=[None, 32, 32, 3])
y_true = tf.placeholder(tf.float32, shape=[None, 10])
hold_prob = tf.placeholder(tf.float32)


def init_weights(shape):
    init_random_dist = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(init_random_dist)


def init_bias(shape):
    init_bias_vals = tf.constant(0.1, shape=shape)
    return tf.Variable(init_bias_vals)


def conv2d(x, W):
    return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')


def max_pool_2by2(x):
    return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],strides=[1, 2, 2, 1], padding='SAME')

def convolutional_layer(input_x, shape):
    W = init_weights(shape)
    b = init_bias([shape[3]])
    return tf.nn.relu(conv2d(input_x, W) + b)


def normal_full_layer(input_layer, size):
    input_size = int(input_layer.get_shape()[1])
    W = init_weights([input_size, size])
    b = init_bias([size])
    return tf.matmul(input_layer, W) + b


convo_1 = convolutional_layer(x, shape=[4, 4, 3, 32])
convo_1_pooling = max_pool_2by2(convo_1)

convo_2 = convolutional_layer(convo_1_pooling, shape=[4, 4, 32, 64])
convo_2_pooling = max_pool_2by2(convo_2)
convo_2_flat = tf.reshape(convo_2_pooling, [-1, 8 * 8 * 64])
full_layer_one = tf.nn.relu(normal_full_layer(convo_2_flat, 1024))
full_one_dropout = tf.nn.dropout(full_layer_one, keep_prob=hold_prob)
y_pred = normal_full_layer(full_one_dropout, 10)
cross_entropy = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=y_true, logits=y_pred))
optimizer = tf.train.AdamOptimizer(learning_rate=0.001)
train = optimizer.minimize(cross_entropy)
init = tf.global_variables_initializer()

with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    for i in range(5000):
        batch = ch.next_batch(100)
        sess.run(train, feed_dict={x: batch[0], y_true: batch[1], hold_prob: 0.5})
        if i % 100 == 0:
            print('Currently on step {}'.format(i))
            print('Accuracy is:')
            # Test the Train Model
            matches = tf.equal(tf.argmax(y_pred, 1), tf.argmax(y_true, 1))
            acc = tf.reduce_mean(tf.cast(matches, tf.float32))
            print(sess.run(acc, feed_dict={x: ch.test_images, y_true: ch.test_labels, hold_prob: 1.0}))
            print('\n')