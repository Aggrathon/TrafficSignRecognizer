import os
import sys
import tensorflow as tf
from tensorflow.python.tools.freeze_graph import freeze_graph
from tensorflow.python.tools.optimize_for_inference_lib import optimize_for_inference
import numpy as np
from model import network, input_fn, model_fn
from predict import PredictionStats, get_session

EXPORT_FOLDER = os.path.join('network', 'export')
INPUT_TENSOR_NAME = 'input'

def export():
    tf.logging.set_verbosity(tf.logging.INFO)
    nn = network()
    td = dict(input=tf.placeholder(tf.float32, [16, 60, 60, 3], INPUT_TENSOR_NAME))
    nn.export_savedmodel(
        EXPORT_FOLDER,
        tf.estimator.export.build_raw_serving_input_receiver_fn(td))

def export2(vertical=5, horizontal=6):
    tf.logging.set_verbosity(tf.logging.INFO)
    inp = tf.placeholder(tf.uint8, [320*240*3], name=INPUT_TENSOR_NAME)
    inp = tf.reshape(inp, [240, 320, 3])
    arr = []
    for i in range(vertical):
        for j in range(horizontal):
            y = int((240.-60.)/(vertical-1)*i)
            x = int((320.-60.)/(horizontal-1)*j)
            arr.append(tf.image.crop_to_bounding_box(inp, y, x, 60, 60))
    model_fn(dict(input=tf.to_float(arr)), None, tf.estimator.ModeKeys.PREDICT)
    sess = get_session()
    tf.train.Saver().save(sess, os.path.join(EXPORT_FOLDER, 'checkpoint.ckpt'))
    tf.train.write_graph(sess.graph_def, EXPORT_FOLDER, 'graph.pbtxt', True)
    sess.close()
    print("Freezing graph")
    lp = get_latest_export()
    ckpt = tf.train.get_checkpoint_state(EXPORT_FOLDER)
    freeze_graph(
        os.path.join(EXPORT_FOLDER, 'graph.pbtxt'),
        None,
        False,
        ckpt.model_checkpoint_path,
        'predictions',
        'save/restore_all',
        'save/Const:0',
        os.path.join(EXPORT_FOLDER, 'fozen.pb'),
        True,
        ''
    )
    input_graph_def = tf.GraphDef()
    with tf.gfile.Open(os.path.join(EXPORT_FOLDER, 'fozen.pb'), "rb") as f:
        input_graph_def.ParseFromString(f.read())
    output_graph = optimize_for_inference(
        input_graph_def,
        ["input"],
        ["predictions"],
        tf.uint8.as_datatype_enum
    )
    with tf.gfile.FastGFile(os.path.join(EXPORT_FOLDER, 'model.pb'), 'w') as f:
        f.write(output_graph.SerializeToString())


def data():
    input = input_fn()[0]['input']
    with tf.Session() as sess:
        sess.run(tf.local_variables_initializer())
        sess.run(tf.global_variables_initializer())
        coord = tf.train.Coordinator()
        tf.train.start_queue_runners(sess, coord)
        arr = sess.run(input)
        np.save(os.path.join(EXPORT_FOLDER, 'data'), arr)
        coord.request_stop()
        coord.join()


def predict():
    print("Creating session")
    sess = tf.Session()
    sess.run(tf.local_variables_initializer())
    sess.run(tf.global_variables_initializer())
    load = tf.saved_model.loader.load(sess, ['serve'], get_latest_export())
    output_tensor = sess.graph.get_tensor_by_name('predictions:0')
    arr = np.load('network/export/data.npy')
    pred = sess.run(output_tensor, {INPUT_TENSOR_NAME+':0': arr})
    for p in pred:
        print("Prediction: %.2f"%p)
    sess.close()


def predict2():
    inp = input_fn()
    input_tensor = inp[0]['input']
    label_tensor = inp[1]['labels']
    print("Creating session")
    sess = tf.Session()
    sess.run(tf.local_variables_initializer())
    sess.run(tf.global_variables_initializer())
    coord = tf.train.Coordinator()
    tf.train.start_queue_runners(sess, coord)
    stats = PredictionStats()
    try:
        load = tf.saved_model.loader.load(sess, ['serve'], get_latest_export())
        output_tensor = sess.graph.get_tensor_by_name('predictions:0')
        print('Predicting images until Ctrl+C is pressed')
        while True:
            data, label = sess.run([input_tensor, label_tensor])
            pred = sess.run(output_tensor, {INPUT_TENSOR_NAME+':0': data})
            stats.add_predictions(pred, label)
    except KeyboardInterrupt:
        pass
    finally:
        coord.request_stop()
        coord.join()
        sess.close()
    print()
    stats.print_result()

def get_latest_export():
    for s in sorted(os.listdir(EXPORT_FOLDER), reverse=True):
        path = os.path.join(EXPORT_FOLDER, s)
        if os.path.isdir(path):
            print('Loading exported model', s)
            return path
    return EXPORT_FOLDER

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Arguments:")
        print(' e  export model')
        print(' p  predict using the latest exported model and training tensors')
        print(' d  export a training tensor as data')
        print(' o  predict using the latest exported model and exported data')
        print(' r  export model for android')
    elif sys.argv[1] == 'e':
        export()
    elif sys.argv[1] == 'p':
        predict2()
    elif sys.argv[1] == 'd':
        data()
    elif sys.argv[1] == 'o':
        predict()
    elif sys.argv[1] == 'r':
        export2()
