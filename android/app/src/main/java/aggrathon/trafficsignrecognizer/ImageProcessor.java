package aggrathon.trafficsignrecognizer;


import android.graphics.Bitmap;
import android.graphics.BitmapFactory;

public class ImageProcessor {

	private boolean initialized;

	public ImageProcessor() {
		initialized = false;
	}

	public void start() {
		//Initialize tf
		initialized = true;
	}

	public void stop() {
		//Deconstruct tf
		initialized = false;
	}

	public Bitmap process(byte[] jpegArray) {
		if(!initialized)
			return null;
		//!!!
		//TODO Process images
		//!!!
		//if no signs return null
		//else return sign area
		//maybe fill screen (needs imageView aspect)
		return BitmapFactory.decodeByteArray(jpegArray, 0, jpegArray.length);
	}
}
