package aggrathon.trafficsignrecognizer;


import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.support.v7.app.AppCompatActivity;

import org.tensorflow.contrib.android.TensorFlowInferenceInterface;

public class ImageProcessor {

	protected static final String MODEL_ASSET_PATH = "saved_model.pb";
	protected static final int NUM_RECOGNITION_SAMPLES_X = 6;
	protected static final int NUM_RECOGNITION_SAMPLES_Y = 5;

	TensorFlowInferenceInterface tf;
	float[] output = new float[NUM_RECOGNITION_SAMPLES_X*NUM_RECOGNITION_SAMPLES_Y];
	char buffer[][][][];

	private boolean initialized;

	public ImageProcessor() {
		initialized = false;
	}

	public void start(AppCompatActivity act) {
		tf = new TensorFlowInferenceInterface(act.getAssets(), MODEL_ASSET_PATH);
		initialized = true;
	}

	public void stop() {
		initialized = false;
		tf.close();
	}

	public Bitmap process(byte[] jpegArray) {
		if(!initialized)
			return null;
		Bitmap bmp = BitmapFactory.decodeByteArray(jpegArray, 0, jpegArray.length);
		if (buffer == null || buffer[0][0][0].length != 3 || buffer[0].length != bmp.getHeight() || buffer[0][0].length != bmp.getWidth()) {
			buffer = new char[1][bmp.getHeight()][bmp.getWidth()][3];
		}
		for(int x = 0; x < bmp.getWidth(); x++) {
			for (int y = 0; y < bmp.getHeight(); y++) {
				int p = bmp.getPixel(x, y);
				buffer[0][y][x][0] = (char)Color.red(p);
				buffer[0][y][x][1] = (char)Color.green(p);
				buffer[0][y][x][2] = (char)Color.blue(p);
			}
		}


		tf.feed("input:0", bmp., 1, bmp.getHeight(), bmp.getWidth(), 3);
		tf.run(new String[] {"predictions:0"}, true);
		tf.fetch("predictions", output);
		boolean pred = false;
		for(int i = 0; i < output.length; i++) {
			if (output[0] > 0.5f) {
				pred = true;
				break;
			}
		}

		if (!pred) {
			bmp.recycle();
			return null;
		}
		//!!!
		//TODO Process images
		//!!!
		//if no signs return null
		//else return sign area
		//maybe fill screen (needs imageView aspect)
		return bmp;
	}
}
