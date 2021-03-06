import os
import sys
import tensorflow as tf
from tensorflow.python.tools.freeze_graph import freeze_graph
from tensorflow.python.tools.optimize_for_inference_lib import optimize_for_inference
from model import network, input_fn, model_fn, CROPPED_IMAGE_SIZE
from predict import PredictionStats, get_session

EXPORT_FOLDER = os.path.join('network', 'export')
INPUT_TENSOR_NAME = 'input'
OUTPUT_TENSOR_NAME = 'predictions'
EXPORTED_MODEL_NAME = os.path.join(EXPORT_FOLDER, 'model.pb')
EXPORTED_MODEL_ANDROID = os.path.join('android', 'app', 'src', 'main', 'assets', 'model.pb')


def export():
    tf.logging.set_verbosity(tf.logging.INFO)
    nn = network()
    inp = tf.placeholder(tf.float32, [None], name=INPUT_TENSOR_NAME)
    inp = tf.reshape(inp, [-1, CROPPED_IMAGE_SIZE, CROPPED_IMAGE_SIZE, 3])
    td = dict(input=inp)
    nn.export_savedmodel(
        EXPORT_FOLDER,
        tf.estimator.export.build_raw_serving_input_receiver_fn(td))

def export2(move=False):
    tf.logging.set_verbosity(tf.logging.INFO)
    inp = tf.placeholder(tf.float32, [None], name=INPUT_TENSOR_NAME)
    inp = tf.reshape(inp, [-1, CROPPED_IMAGE_SIZE, CROPPED_IMAGE_SIZE, 3])
    model_fn(dict(input=inp), None, tf.estimator.ModeKeys.PREDICT)
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
        OUTPUT_TENSOR_NAME,
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
        [INPUT_TENSOR_NAME],
        [OUTPUT_TENSOR_NAME],
        tf.float32.as_datatype_enum
    )
    with tf.gfile.FastGFile(EXPORTED_MODEL_NAME, 'w') as f:
        f.write(output_graph.SerializeToString())
    if move:
        try:
            os.remove(EXPORTED_MODEL_ANDROID)
        except:
            pass
        os.rename(EXPORTED_MODEL_NAME, EXPORTED_MODEL_ANDROID)

def predict():
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
        output_tensor = sess.graph.get_tensor_by_name(OUTPUT_TENSOR_NAME+':0')
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
        print(' r  export model for android')
        print(' t  export model for android and move it to the app assets folder')
        print(' p  predict using the latest exported model and training tensors')
    elif sys.argv[1] == 'e':
        export()
    elif sys.argv[1] == 'p':
        predict()
    elif sys.argv[1] == 'r':
        export2()
    elif sys.argv[1] == 't':
        export2(move=True)
