package aggrathon.trafficsignrecognizer;


import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.support.v7.app.AppCompatActivity;
import android.util.Log;

import org.tensorflow.contrib.android.TensorFlowInferenceInterface;

import java.util.ArrayList;
import java.util.concurrent.Future;
import java.util.concurrent.LinkedBlockingDeque;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

public class ImageProcessor {

	protected static final String MODEL_ASSET_PATH = "model.pb";
	protected static final int NUM_RECOGNITION_SAMPLES_X = 7;
	protected static final int NUM_RECOGNITION_SAMPLES_Y = 5;
	protected static final String INPUT_TENSOR_NAME = "input:0";
	protected static final String OUTPUT_TENSOR_NAME = "predictions:0";

	TensorFlowInferenceInterface tf;
	float[] output = new float[NUM_RECOGNITION_SAMPLES_X*NUM_RECOGNITION_SAMPLES_Y];
	float buffer[];
	boolean initialized;
	boolean ready = false;
	ThreadPoolExecutor threadPoolExecutor;
	ArrayList<Future> futures;
	long startMillis;

	public ImageProcessor() {
		initialized = false;
		ready = false;
		futures = new ArrayList<>();
	}

	public void start(AppCompatActivity act) {
		tf = new TensorFlowInferenceInterface(act.getAssets(), MODEL_ASSET_PATH);
		int cores = Runtime.getRuntime().availableProcessors();
		threadPoolExecutor = new ThreadPoolExecutor(cores, cores, 20, TimeUnit.SECONDS, new LinkedBlockingDeque<Runnable>());
		initialized = true;
		ready = true;
	}

	public void stop() {
		ready = false;
		initialized = false;
		futures.clear();
		if (tf != null) tf.close();
		tf = null;
		if(threadPoolExecutor != null) threadPoolExecutor.shutdown();
		threadPoolExecutor = null;
	}

	public  boolean checkReady() {
		return initialized && ready;
	}


	public Bitmap process(byte[] img) {
		startMillis = System.currentTimeMillis();
		Bitmap bmp = null;
		if(checkCancel(bmp, false))
			return null;
		ready = false;
		try {
			//Decode Image
			bmp = BitmapFactory.decodeByteArray(img, 0, img.length);
			img = null;
			Bitmap bmp2 = Bitmap.createScaledBitmap(bmp, (int)((float)bmp.getWidth()/bmp.getHeight()*240), 240, true);
			if(checkCancel(bmp, false))
				return null;

			//Fill buffer
			if (buffer == null) {
				buffer = new float[3 * 60 * 60 * NUM_RECOGNITION_SAMPLES_X * NUM_RECOGNITION_SAMPLES_Y];
			}
			futures.clear();
			for (int i = 0; i < NUM_RECOGNITION_SAMPLES_X; i++) {
				for (int j = 0; j < NUM_RECOGNITION_SAMPLES_Y; j++) {
					int y = getCropY(bmp2, 60, j);
					int x = getCropX(bmp2, 60, i);
					if (threadPoolExecutor == null) {
						checkCancel(bmp, true);
						return null;
					}
					futures.add(threadPoolExecutor.submit(new ImageCropper(this, bmp2, x, y, 60, 60, 60*60*3*(i*NUM_RECOGNITION_SAMPLES_Y+j))));
				}
			}
			for (int i = 0; i < futures.size(); i++)
				if(initialized)
					futures.get(i).get();
			bmp2.recycle();
			if(checkCancel(bmp, false))
				return null;
			Log.d("tensorflow", "Filling buffers took "+(System.currentTimeMillis()-startMillis)+" ms");

			//Call tensorflow
			tf.feed(INPUT_TENSOR_NAME, buffer, (long) (buffer.length));
			tf.run(new String[]{OUTPUT_TENSOR_NAME});
			tf.fetch(OUTPUT_TENSOR_NAME, output);

			//Check result
			int minX = -1000;
			int minY = -1000;
			int maxX = -1000;
			int maxY = -1000;
			int scaledCropSize = 60*bmp.getHeight()/240;
			for (int i = 0; i < output.length; i++) {
				if (output[i] > 0.5f) {
					int x = getCropX(bmp, scaledCropSize, i/NUM_RECOGNITION_SAMPLES_Y)-scaledCropSize/4;
					int y = getCropX(bmp, scaledCropSize, i%NUM_RECOGNITION_SAMPLES_Y)-scaledCropSize/4;
					if (minX == -1000 || x < minX)
						minX = x;
					if (minY == -1000 || y < minY)
						minY = y;
					x += scaledCropSize+scaledCropSize/2;
					y += scaledCropSize+scaledCropSize/2;
					if (maxX == -1000 || x > maxX)
						maxX = x;
					if (maxY == -1000 || y > maxY)
						maxY = y;
				}
			}
			if (minX == -1000) {
				Log.d("tensorflow", "Classification (no sign) took "+(System.currentTimeMillis()-startMillis)+" ms");
				checkCancel(bmp, true);
				return null;
			}

			//Crop the original image to mostly show signs
			float w = maxX-minX;
			float h = minX-minY;
			if (w > 1.5*h) {
				minY -= scaledCropSize/2;
				maxY += scaledCropSize/2;
			}
			if (h > 1.5*w) {
				minX -= scaledCropSize/2;
				maxX += scaledCropSize/2;
			}
			if (minX < 0) minX = 0;
			if (minY < 0) minY = 0;
			if (maxX >= bmp.getWidth()) maxX = bmp.getWidth() -1;
			if (maxY >= bmp.getHeight()) maxY = bmp.getHeight() -1;
			ready = true;
			bmp = Bitmap.createBitmap(bmp, minX, minY, maxX-minX, maxY-minY);
			Log.d("tensorflow", "Classification (has sign) took "+(System.currentTimeMillis()-startMillis)+" ms");
			return bmp;
		}
		catch (Exception e) {
			Log.e("tensorflow", "Couldn't run the tensorflow graph ("+e.toString()+")");
			checkCancel(bmp, true);
			return null;
		}
	}

	private boolean checkCancel(Bitmap bmp, boolean force) {
		if(!initialized || force) {
			if(bmp != null) bmp.recycle();
			ready = true;
			return true;
		}
		return false;
	}

	private int getCropX(Bitmap bmp, int cropWidth, int x) {
		return Math.min(bmp.getWidth()-cropWidth-1, (int)((float)(bmp.getWidth() - cropWidth) * (float)x / (float)(NUM_RECOGNITION_SAMPLES_X - 1)));
	}

	private int getCropY(Bitmap bmp, int cropHeight, int y) {
		return Math.min(bmp.getHeight()-cropHeight-1, (int)((float)(bmp.getHeight() - cropHeight) * (float)y / (float)(NUM_RECOGNITION_SAMPLES_Y - 1)));
	}

	private class ImageCropper implements Runnable {

		ImageProcessor imgProc;
		Bitmap bmp;
		int x;
		int y;
		int width;
		int height;
		int index;

		public ImageCropper(ImageProcessor imgProc, Bitmap bmp, int x, int y, int width, int height, int index) {
			this.bmp = bmp;
			this.imgProc = imgProc;
			this.x = x;
			this.y = y;
			this.width = width;
			this.height = height;
			this.index = index;
		}

		@Override
		public void run() {
			for (int y = 0; y < height; y++) {
				for (int x = 0; x < width; x++) {
					if(!imgProc.initialized)
						return;
					int p = bmp.getPixel(x+this.x, y+this.y);
					imgProc.buffer[index + 0] = (float) Color.red(p) / 255f;
					imgProc.buffer[index + 1] = (float) Color.green(p) / 255f;
					imgProc.buffer[index + 2] = (float) Color.blue(p) / 255f;
					index += 3;
				}
			}
		}
	}
}
