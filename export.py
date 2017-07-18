import os
import sys
import tensorflow as tf
import numpy as np
from model import network, input_fn

def export():
    tf.logging.set_verbosity(tf.logging.INFO)
    nn = network()
    td = dict(input=tf.placeholder(tf.float32, [None, 60, 60, 3]))
    nn.export_savedmodel(
        os.path.join('network', 'export'),
        tf.estimator.export.build_raw_serving_input_receiver_fn(td))

def data():
    input = input_fn()[0]['input']
    with tf.Session() as sess:
        sess.run(tf.local_variables_initializer())
        sess.run(tf.global_variables_initializer())
        coord = tf.train.Coordinator()
        tf.train.start_queue_runners(sess, coord)
        arr = sess.run(input)
        np.save('network/export/data', arr)
        coord.request_stop()
        coord.join()


def predict():
    #input_data = input_fn()['input']
    print("Creating session")
    sess = tf.Session()
    #sess.run(tf.global_variables_initializer())
    #coord = tf.train.Coordinator()
    #tf.train.start_queue_runners(sess, coord)
    try:
        load = tf.saved_model.loader.load(sess, ['serve'], os.path.join('network', 'export', '1500023418'))
        #print(load)
        #return
        input_tensor = sess.graph.get_tensor_by_name('Placeholder:0')[0]
        output_tensor = sess.graph.get_tensor_by_name('predictions:0')[0]
        print('Predicting')
        while True:
            #arr = sess.run(input_data)
            #print(arr)
            arr = np.zeros([1,60,60,3])
            print(arr)
            np.save('network/export/data', arr)
            print(sess.run(output_tensor))#, {input_tensor: arr}))
    except KeyboardInterrupt:
        pass
    finally:
        #coord.join()
        sess.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Arguments:")
        print('  e\texport')
        print('  p\tpredict')
        print('  d\tdata')
    elif sys.argv[1] == 'e':
        export()
    elif sys.argv[1] == 'p':
        predict()
    elif sys.argv[1] == 'd':
        data()