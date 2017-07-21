package aggrathon.trafficsignrecognizer;


import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.support.v7.app.AppCompatActivity;

import org.tensorflow.contrib.android.TensorFlowInferenceInterface;

public class ImageProcessor {

	protected static final String MODEL_ASSET_PATH = "model.pb";
	protected static final int NUM_RECOGNITION_SAMPLES_X = 6;
	protected static final int NUM_RECOGNITION_SAMPLES_Y = 5;

	TensorFlowInferenceInterface tf;
	float[] output = new float[NUM_RECOGNITION_SAMPLES_X*NUM_RECOGNITION_SAMPLES_Y];
	byte buffer[];

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
		int targetWidth = bmp.getHeight()*320/240;
		int targetHeight = bmp.getHeight();
		if (targetWidth > bmp.getWidth()) {
			targetWidth = bmp.getWidth();
			targetHeight = bmp.getWidth()*240/320;
		}
		Bitmap bmp1 = Bitmap.createBitmap(bmp, (bmp.getWidth()-targetWidth)/2, (bmp.getHeight()-targetHeight)/2, targetWidth, targetHeight);
		Bitmap bmp2 = Bitmap.createScaledBitmap(bmp1, 320, 240, true);
		if (buffer == null) {
			buffer = new byte[3 * 240 * 320];
		}
		for(int x = 0; x < 320; x++) {
			for (int y = 0; y < 240; y++) {
				int p = bmp2.getPixel(x, y);
				buffer[y*320*3 + x*3 + 0] = (byte)Color.red(p);
				buffer[y*320*3 + x*3 + 1] = (byte)Color.green(p);
				buffer[y*320*3 + x*3 + 2] = (byte)Color.blue(p);
			}
		}
		bmp2.recycle();

		tf.feed("input:0", buffer, (long)(320*240*3));
		tf.run(new String[] {"predictions:0"}, true);
		tf.fetch("predictions:0", output);
		boolean pred = false;
		for(int i = 0; i < output.length; i++) {
			if (output[0] > 0.5f) {
				pred = true;
				break;
			}
		}

		if (!pred) {
			bmp.recycle();
			bmp1.recycle();
			return null;
		}
		//!!!
		//TODO Process images
		//!!!
		//if no signs return null
		//else return sign area
		//maybe fill screen (needs imageView aspect)
		return bmp1;
	}
}
