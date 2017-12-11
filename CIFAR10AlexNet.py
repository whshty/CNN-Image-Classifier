import pickle
import numpy as np
from sklearn.utils import shuffle
import tensorflow as tf
import time
import AlexNet as AlexNet
from sklearn.model_selection import train_test_split

LabelNames = ['Airplane', 'Automobile', 'Bird', 'Cat', 'Deer', 'Dog', 'Frog', 'Horse', 'Ship', 'Truck']
CIFARPATH = 'cifar-10-batches-py'

totalBatchCount = 5

trainInput, trainLabel = [], []

for i in range(1, totalBatchCount + 1):
    with open(CIFARPATH + '/data_batch_' + str(i), mode='rb') as File:
        Batch = pickle.load(File, encoding='latin1')
    if i == 1:
        trainInput = Batch['data'].reshape((len(Batch['data']), 3, 32, 32)).transpose(0, 2, 3, 1)
        trainLabel = Batch['labels']
    else:
        trainInputTemp, trainLabelTemp = [], []
        trainInputTemp = Batch['data'].reshape((len(Batch['data']), 3, 32, 32)).transpose(0, 2, 3, 1)
        trainLabelTemp = Batch['labels']
        trainInput = np.concatenate((trainInput, trainInputTemp), axis=0)
        trainLabel = np.concatenate((trainLabel, trainLabelTemp), axis=0)


assert (len(trainInput) == len(trainLabel))
NumClass = len(set(trainLabel))

# Print Data Characteristics
print("Training Set:{} Samples".format(len(trainInput)))
print("Image Shape:{}".format(trainInput[0].shape))
print('Number of Classes: {}'.format(dict(zip(*np.unique(trainLabel, return_counts=True)))))
print('First 20 Labels: {}'.format(trainLabel[:20]))

with open(CIFARPATH + '/test_batch', mode='rb') as File:
    Batch = pickle.load(File, encoding='latin1')
# load the training data
testInput = Batch['data'].reshape((len(Batch['data']), 3, 32, 32)).transpose(0, 2, 3, 1)
testLabel = Batch['labels']

trainInput, trainLabel = shuffle(trainInput, trainLabel)
testInput, testLabel = shuffle(testInput, testLabel)

trainInput, XVal, trainLabel, YVal = train_test_split(trainInput, trainLabel, test_size=0.10, random_state=0)
print('Training Data Randomized and Split for Validation')
print('Training Data Size:' + str(trainInput.shape))
print('Validation Data Size:' + str(XVal.shape))


def evaluate(X, Y, Sess):
    totalAcc = 0
    totalLoss = 0
    for Offset in range(0, X.shape[0], BatchSize):
        End = Offset + BatchSize
        XBatch = X[Offset:End]
        YBatch = Y[Offset:End]
        Loss, Acc = Sess.run([LossOp, AccuracyOp], feed_dict={features: XBatch, labels: YBatch})
        totalLoss += (Loss * XBatch.shape[0])
        totalAcc += (Acc * XBatch.shape[0])

    # Return Loss and Accuracy
    return totalLoss / X.shape[0], totalAcc / X.shape[0]

Epochs = 20
BatchSize = 128

trainedWeight = np.load('bvlc_alexnet.npy', encoding='bytes').item()

features = tf.placeholder(tf.float32, (None, 32, 32, 3))
labels = tf.placeholder(tf.int64, None)
resizedImage = tf.image.resize_images(features, (227, 227))

N7 = AlexNet.AlexNetCIFAR10(resizedImage, trainedWeight)
N7 = tf.stop_gradient(N7)
Shape = (N7.get_shape().as_list()[-1], NumClass)
W8 = tf.Variable(tf.truncated_normal(Shape, stddev=1e-2))
B8 = tf.Variable(tf.zeros(NumClass))
Logits = tf.nn.xw_plus_b(N7, W8, B8)


crossEntropy = tf.nn.sparse_softmax_cross_entropy_with_logits(logits=Logits, labels=labels)
LossOp = tf.reduce_mean(crossEntropy)
Opt = tf.train.AdamOptimizer()
TrainOp = Opt.minimize(LossOp, var_list=[W8, B8])
InitOp = tf.global_variables_initializer()
Preds = tf.arg_max(Logits, 1)
AccuracyOp = tf.reduce_mean(tf.cast(tf.equal(Preds, labels), tf.float32))

with tf.Session() as sess:
    sess.run(InitOp)
    for step in range(Epochs):
        trainInput, trainLabel = shuffle(trainInput, trainLabel)
        T0 = time.time()
        for Offset in range(0, trainInput.shape[0], BatchSize):
            End = Offset + BatchSize
            sess.run(TrainOp, feed_dict={features: trainInput[Offset:End], labels: trainLabel[Offset:End]})

        ValLoss, ValAcc = evaluate(XVal, YVal, sess)
        print("Epoch {}, Accuracy {}".format(step + 1, ValAcc))
        # print("Time: %.3f seconds" % (time.time() - T0))
        # print("Validation Loss =", ValLoss)
        # print("Validation Accuracy =", ValAcc)
