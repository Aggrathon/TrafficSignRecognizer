package aggrathon.trafficsignrecognizer;


import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.support.v7.app.AppCompatActivity;

import org.tensorflow.contrib.android.TensorFlowInferenceInterface;

public class ImageProcessor {

	protected static final String MODEL_ASSET_PATH = "model.pb";
	protected static final int NUM_RECOGNITION_SAMPLES_X = 8;
	protected static final int NUM_RECOGNITION_SAMPLES_Y = 6;
	protected static final String INPUT_TENSOR_NAME = "input:0";
	protected static final String OUTPUT_TENSOR_NAME = "predictions:0";

	TensorFlowInferenceInterface tf;
	float[] output = new float[NUM_RECOGNITION_SAMPLES_X*NUM_RECOGNITION_SAMPLES_Y];
	float buffer[];

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
		tf = null;
	}

	public Bitmap process(byte[] jpegArray) {
		if(!initialized)
			return null;
		Bitmap bmp = BitmapFactory.decodeByteArray(jpegArray, 0, jpegArray.length);
		Bitmap bmp2 = Bitmap.createScaledBitmap(bmp, (int)((float)bmp.getWidth()/bmp.getHeight()*240), 240, true);
		if (buffer == null) {
			buffer = new float[3 * 60 * 60 * NUM_RECOGNITION_SAMPLES_X * NUM_RECOGNITION_SAMPLES_Y];
		}
		int index = 0;
		for (int i = 0; i < NUM_RECOGNITION_SAMPLES_X; i++) {
			for (int j = 0; j < NUM_RECOGNITION_SAMPLES_Y; j++) {
				int yOffset = Math.min(bmp2.getHeight()-60, (int)((bmp2.getHeight() - 60.0f) * j / (NUM_RECOGNITION_SAMPLES_Y - 1)));
				int xOffset = Math.min(bmp2.getWidth()-60, (int)((bmp2.getWidth() - 60.0f) * i / (NUM_RECOGNITION_SAMPLES_X - 1)));
				for (int y = 0; y < 60; y++) {
					for (int x = 0; x < 60; x++) {
						int p = bmp2.getPixel(x+xOffset, y+yOffset);
						buffer[index + 0] = (float) Color.red(p) / 255f;
						buffer[index + 1] = (float) Color.green(p) / 255f;
						buffer[index + 2] = (float) Color.blue(p) / 255f;
						index += 3;
					}
				}
			}
		}
		bmp2.recycle();

		if(tf == null)
			return null;
		tf.feed(INPUT_TENSOR_NAME, buffer, (long)(buffer.length));
		tf.run(new String[] {OUTPUT_TENSOR_NAME});
		tf.fetch(OUTPUT_TENSOR_NAME, output);
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
