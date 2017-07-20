package aggrathon.trafficsignrecognizer;


import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.ImageFormat;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.media.Image;
import android.media.ImageReader;
import android.os.Handler;
import android.os.HandlerThread;
import android.support.annotation.NonNull;
import android.support.v7.app.AppCompatActivity;
import android.util.Log;
import android.util.Size;
import android.widget.ImageView;
import android.widget.Toast;

import java.nio.ByteBuffer;
import java.util.Arrays;

public class ImageThread {

	protected static final long IMAGE_MIN_INTERVAL = 100;

	private boolean shouldStop;
	private long prevTime;

	private ImageView imageView;
	private AppCompatActivity activity;
	private CameraManager manager;
	private HandlerThread thread;
	private Handler handler;
	private ImageReader imageReader;
	private CameraCaptureSession cameraSession;
	private Bitmap bmp;


	public ImageThread(ImageView imageView, AppCompatActivity activity) {
		shouldStop = false;
		this.imageView = imageView;
		this.activity = activity;
		manager = (CameraManager) activity.getSystemService(Context.CAMERA_SERVICE);
		start();
	}

	private void cameraDisconnectAccessException() {
		cameraDisconnect("Access to the camera denied (CameraAccessException)", true);
	}

	private void cameraDisconnect(String msg, boolean error) {
		if(error)
			Log.e("camera", msg);
		else
			Log.i("camera", msg);
		Toast.makeText(imageView.getContext(), msg, Toast.LENGTH_SHORT).show();
		stop();
	}


	public void stop() {
		shouldStop = true;

		if(cameraSession != null) {
			cameraSession.close();
			cameraSession = null;
		}
		if (imageReader != null) {
			imageReader.close();
			imageReader = null;
		}
		if(bmp != null) {
			bmp.recycle();
			bmp = null;
			activity.runOnUiThread(new Runnable() {
				@Override
				public void run() {
					imageView.setImageResource(R.drawable.sign_icon);
				}
			});
		}

		if(thread != null) {
			handler = null;
			HandlerThread t = thread;
			thread = null;
			t.quitSafely();
			try {
				t.join();
			}
			catch (InterruptedException e) {
				Log.e("camera", "Thread interrupted");
			}
		}
		//TODO show reconnect button
	}

	public void start() {
		prevTime = System.currentTimeMillis()-IMAGE_MIN_INTERVAL;
		// Start background thread
		thread = new HandlerThread("ImageManager");
		thread.start();
		handler = new Handler(thread.getLooper());
		//TODO hide reconnect button

		try {
			//Find the right camera and characteristics
			String cameraId = getCorrectCamera(manager);
			if (cameraId == null) {
				cameraDisconnect("No suitable camera found", true);
				return;
			}
			CameraCharacteristics characteristics = manager.getCameraCharacteristics(cameraId);
			Size captureSize = getCorrectSize(characteristics);
			if (captureSize == null) {
				cameraDisconnect("No suitable camera size found", true);
				return;
			}
			openCamera(cameraId, captureSize);
		}
		catch (SecurityException e) {
			cameraDisconnect("Access to the camera not granted", true);
		}
		catch (CameraAccessException e) {
			cameraDisconnectAccessException();
		}
	}


	private void openCamera(String id, final Size captureSize) throws SecurityException, CameraAccessException {
		manager.openCamera(id, new CameraDevice.StateCallback() {
			@Override
			public void onOpened(@NonNull final CameraDevice cameraDevice) {
				createSession(cameraDevice, captureSize);
			}

			@Override
			public void onDisconnected(@NonNull CameraDevice cameraDevice) {
				Log.d("camera", "Camera disconnected");
				stop();
			}

			@Override
			public void onError(@NonNull CameraDevice cameraDevice, int i) {
				switch (i) {
					case CameraDevice.StateCallback.ERROR_CAMERA_IN_USE:
						cameraDisconnect("Camera already in use", true);
						break;
					case CameraDevice.StateCallback.ERROR_MAX_CAMERAS_IN_USE:
						cameraDisconnect("Max cameras in use", true);
						break;
					case CameraDevice.StateCallback.ERROR_CAMERA_DISABLED:
						cameraDisconnect("Camera is disabled", true);
						break;
					case CameraDevice.StateCallback.ERROR_CAMERA_DEVICE:
						cameraDisconnect("Camera error", true);
						break;
					case CameraDevice.StateCallback.ERROR_CAMERA_SERVICE:
						cameraDisconnect("Camera service error", true);
						break;
					default:
						cameraDisconnect("Unknown camera error", true);
						break;
				}
			}
		}, handler);
	}

	private void createSession(final CameraDevice cameraDevice, final Size captureSize) {
		try {
			//Build ImageReader, CaptureRequest and CameraSession
			CaptureRequest.Builder builder = cameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
			imageReader =  ImageReader.newInstance(captureSize.getWidth(), captureSize.getHeight(), ImageFormat.JPEG, 2);
			builder.addTarget(imageReader.getSurface());
			builder.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_AUTO); //all auto
			builder.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE); //Auto focus on
			builder.set(CaptureRequest.FLASH_MODE, CaptureRequest.FLASH_MODE_OFF); //Flash off
			builder.set(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_ON); //Exposure auto
			builder.set(CaptureRequest.CONTROL_AWB_MODE, CaptureRequest.CONTROL_AWB_MODE_AUTO); //WB auto
			final CaptureRequest captureRequest = builder.build();
			cameraDevice.createCaptureSession(Arrays.asList(imageReader.getSurface()), new CameraCaptureSession.StateCallback() {
				@Override
				public void onConfigured(@NonNull CameraCaptureSession cameraCaptureSession) {
					if (cameraDevice == null) {
						stop();
						return;
					}
					cameraSession = cameraCaptureSession;
					captureImages(captureRequest);
				}

				@Override
				public void onConfigureFailed(@NonNull CameraCaptureSession cameraCaptureSession) {
					cameraDisconnect("Camera configuration failed", true);
					stop();
				}
			}, handler);
		}
		catch (CameraAccessException e) {
			cameraDisconnectAccessException();
		}
	}

	private void captureImages(final CaptureRequest request) {
		if(shouldStop || cameraSession == null || imageReader == null || thread == null || handler == null) {
			stop();
			return;
		}
		try {
			imageReader.setOnImageAvailableListener(new ImageReader.OnImageAvailableListener() {
				@Override
				public void onImageAvailable(ImageReader imageReader) {
					if(shouldStop)
						return;
					Image img = imageReader.acquireLatestImage();
					ByteBuffer buf = img.getPlanes()[0].getBuffer();
					byte[] bb = new byte[buf.remaining()];
					buf.get(bb);
					img.close();
					if(shouldStop)
						return;
					if(bmp != null)
						bmp.recycle();
					bmp = BitmapFactory.decodeByteArray(bb, 0, bb.length);
					//!!!
					//TODO Proccess images
					//!!!
					activity.runOnUiThread(new Runnable() {
						@Override
						public void run() {
							imageView.setImageBitmap(bmp);
						}
					});
					//Run interval is IMAGE_MIN_INTERVAL/1000 s
					long delay = prevTime + IMAGE_MIN_INTERVAL - System.currentTimeMillis();
					prevTime = System.currentTimeMillis();
					if (delay < 0)
						delay = 0;
					handler.postDelayed(new Runnable() {
						@Override
						public void run() {
							try {
								cameraSession.capture(request, null, handler);
							}
							catch (CameraAccessException e) {
								cameraDisconnectAccessException();
							}
						}
					}, delay);
				}
			}, handler);
			cameraSession.capture(request, null, handler);
		}
		catch (CameraAccessException e) {
			cameraDisconnectAccessException();
		}
	}


	/**
	 * Gets the first camera that isn't a front facing camera
	 * @param manager
	 * @return
	 * @throws CameraAccessException
	 */
	protected String getCorrectCamera(CameraManager manager) throws CameraAccessException {
		for (String id : manager.getCameraIdList()) {
			CameraCharacteristics characteristics = manager.getCameraCharacteristics(id);
			Integer facing = characteristics.get(CameraCharacteristics.LENS_FACING);
			if (facing != null && facing != CameraCharacteristics.LENS_FACING_FRONT) {
				return id;
			}
		}
		return null;
	}

	/***
	 * Gets the size from a camera that most closely matches an HD resolution with the aspect 320:240
	 * @param cc The camera characteristics
	 * @return The most optimal size (null if no sizes available at all)
	 */
	protected Size getCorrectSize(CameraCharacteristics cc) {
		int targetWidth = 320*6;
		int targetHeight = 240*6;
		Size current = null;
		StreamConfigurationMap scm = cc.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
		for (Size s : scm.getOutputSizes(ImageReader.class)) {
			if (current == null)
				current = s;
			else {
				if (current.getHeight()*current.getWidth() < s.getHeight()*s.getWidth()) {
					if (current.getHeight() < targetHeight || current.getWidth() < targetWidth)
						current = s;
				}
				else {
					if (s.getHeight() >= targetHeight && s.getWidth() >= targetWidth)
						current = s;
				}
			}
		}
		return current;
	}

}
