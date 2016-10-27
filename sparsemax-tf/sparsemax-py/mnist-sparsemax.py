import argparse

# Import data
from tensorflow.examples.tutorials.mnist import input_data
from tensorflow.python.framework import ops # Used to define own op

import tensorflow as tf

import sparsemax
import numpy as np

FLAGS = None

###################################################################################
# Define new sparsemax ops
###################################################################################



###################################################################################
# Andreas sparsemax_forward function
###################################################################################

def forward(z, q):
    """Calculates the sparsemax loss function
    this will process a 2d-array $z$, where axis 1 (each row) is assumed to be
    the the z-vector. q is a binary matrix of same shape, containing the labels
    """

    # Calculate q^T * z
    z_k = np.sum(q * z, axis=1)

    # calculate sum over S(z)
    p = sparsemax.forward(z)
    s = p > 0
    # z_i^2 - tau(z)^2 = p_i (2 * z_i - p_i) for i \in S(z)
    S_sum = np.sum(s * p * (2 * z - p), axis=1)

    # because q is binary, sum([q_1^2, q_2^2, ...]) is just sum(q)
    q_norm = np.sum(q, axis=1)

    return -z_k + 0.5 * S_sum + 0.5 * q_norm

def grad(z, q):
    return -q + sparsemax.forward(z)

def _grad(op, grad):
  Z = op.inputs[0]
  q = op.inputs[1]
  result = -q + sparsemax.forward(Z.eval()) #!!!! It seems that Z.eval() causes the bug
  return [result, None]

###################################################################################
# Define new op and gradient in Python
###################################################################################


def py_func(func, inp, Tout, stateful=True, name=None, grad=None):
    
  # Need to generate a unique name to avoid duplicates:
  rnd_name = 'PyFuncGrad' + str(np.random.randint(0, 1E+8))

  tf.RegisterGradient(rnd_name)(grad)  # see _MySquareGrad for grad example
  g = tf.get_default_graph()
  with g.gradient_override_map({"PyFunc": rnd_name}):
    result = tf.py_func(func, inp, Tout, stateful=stateful, name=name)
    return result


def sparsemax_forward(Z, q, name=None):
    
  with ops.op_scope([Z, q], name, "SparseMaxGrad") as name:

    # py_func takes a list of tensors and a function that takes np arrays as inputs
    # and returns np arrays as outputs
    forward_pass = py_func(forward,
              [Z, q],
              [tf.float64],
              name=name,
              grad=_grad)  # <-- here's the call to the gradient
    return forward_pass[0]

###################################################################################
###################################################################################
###################################################################################
###################################################################################

def main(_):
  mnist = input_data.read_data_sets(FLAGS.data_dir, one_hot=True)

  with tf.Session() as sess:
    # Create the model
    x = tf.placeholder(tf.float64, [None, 784], name="input.x")
    W = tf.cast(tf.Variable(tf.zeros([784, 10])), tf.float64, name="weights")
    b = tf.cast(tf.Variable(tf.zeros([10])), tf.float64, name="biases")
    y = tf.matmul(x, W) + b

    # Define loss and optimizer
    y_ = tf.placeholder(tf.float64, [None, 10])
    tf.initialize_all_variables().run()
    cross_entropy = tf.reduce_mean(sparsemax_forward(y, y_))
    train_step = tf.train.GradientDescentOptimizer(0.5).minimize(cross_entropy)
    # Train
    for _ in range(100):
      batch_xs, batch_ys = mnist.train.next_batch(100)
      # DEBUG
      #print("batch_xs:")
      #print(batch_xs.shape)
      #print("batch_ys:")
      #print(batch_ys.shape)
      #print("Sparsemax forward: ")
      print(sess.run(cross_entropy, feed_dict={x: batch_xs, y_: batch_ys}))
      sess.run(train_step, feed_dict={x: batch_xs, y_: batch_ys})

    # Test trained model
    #correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(y_, 1))
    #accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
    #print(sess.run(accuracy, feed_dict={x: mnist.test.images,
    #                                   y_: mnist.test.labels}))
    #
    



if __name__ == '__main__':
  print("BUAHAA")
  parser = argparse.ArgumentParser()
  parser.add_argument('--data_dir', type=str, default='/tmp/data',
                      help='Directory for storing data')
  FLAGS = parser.parse_args()
  tf.app.run()