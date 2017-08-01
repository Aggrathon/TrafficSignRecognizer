package aggrathon.trafficsignrecognizer;


import android.content.Context;
import android.graphics.Bitmap;
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
import android.util.Log;
import android.util.Size;
import android.view.Surface;
import android.view.SurfaceHolder;
import android.widget.Toast;

import java.nio.ByteBuffer;
import java.util.Arrays;

public class ImageThread {

	private boolean shouldStop;

	private String cameraId;
	private SurfaceHolder liveSurfaceHolder;
	private Surface liveSurface;
	private MainActivity activity;
	private ImageProcessor processor;
	private CameraManager manager;
	private HandlerThread thread1;
	private HandlerThread thread2;
	private Handler handler1;
	private Handler handler2;
	private ImageReader imageReader;
	private CameraCaptureSession cameraSession;
	private Size captureSize;
	private CaptureRequest captureRequest;
	private int cameraSensorOrientation;


	public ImageThread(SurfaceHolder liveView, MainActivity activity) {
		shouldStop = false;
		liveSurfaceHolder = liveView;
		this.activity = activity;
		processor = new ImageProcessor();
		manager = (CameraManager) activity.getSystemService(Context.CAMERA_SERVICE);


		try {
			//Find the right camera and characteristics
			cameraId = getCorrectCamera(manager);
			if (cameraId == null) {
				cameraDisconnect("No suitable camera found", true);
				return;
			}
			CameraCharacteristics characteristics = manager.getCameraCharacteristics(cameraId);
			captureSize = getCorrectSize(characteristics);
			if (captureSize == null) {
				cameraDisconnect("No suitable camera size found", true);
				return;
			}
			cameraSensorOrientation = characteristics.get(CameraCharacteristics.SENSOR_ORIENTATION);
		}
		catch (CameraAccessException e) {
			cameraDisconnectAccessException();
		}
		catch (NullPointerException e) {
			Log.i("camera", "Could not get the camera orientation");
		}
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
		if(!shouldStop) {
			stop();
			Toast.makeText(activity, msg, Toast.LENGTH_SHORT).show();
			//TODO Show camera reconnect popup
		}
	}

	public boolean isStopped() {
		return shouldStop ||
				thread1 == null ||
				thread2 == null ||
				!thread1.isAlive() ||
				!thread2.isAlive();
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

		processor.stop();

		HandlerThread t1 = thread1;
		HandlerThread t2 = thread2;
		handler1 = null;
		handler2 = null;
		thread1 = null;
		thread2 = null;

		if (t1 != null)
			t1.quitSafely();
		if (t2 != null)
			t2.quitSafely();
		if (t1 != null) {
			try {
				t1.join();
			}
			catch (InterruptedException e) {
				Log.e("camera", "Thread interrupted");
			}
		}
		if (t2 != null) {
			try {
				t2.join();
			}
			catch (InterruptedException e) {
				Log.e("camera", "Thread interrupted");
			}
		}
	}

	public void start() {
		// Start background threads
		thread1 = new HandlerThread("ImageManager");
		thread1.start();
		handler1 = new Handler(thread1.getLooper());
		thread2 = new HandlerThread("ImageManager");
		thread2.start();
		handler2 = new Handler(thread1.getLooper());
		handler2.post(new Runnable() {
			@Override
			public void run() {
				processor.start(activity);
			}
		});
		final CameraStateCallback cb = new CameraStateCallback(this);
		liveSurfaceHolder.addCallback(new SurfaceHolder.Callback() {
			@Override
			public void surfaceCreated(SurfaceHolder surfaceHolder) {
				liveSurface = liveSurfaceHolder.getSurface();
				if (cameraId == null || manager == null) {
					cameraDisconnect("Camera not setup", true);
					return;
				}
				try {
					manager.openCamera(cameraId, cb, handler1);
				} catch (SecurityException e) {
					cameraDisconnect("Access to the camera not granted", true);
				} catch (CameraAccessException e) {
					cameraDisconnectAccessException();
				}
			}
			@Override
			public void surfaceChanged(SurfaceHolder surfaceHolder, int i, int i1, int i2) { }
			@Override
			public void surfaceDestroyed(SurfaceHolder surfaceHolder) { }
		});
		liveSurfaceHolder.setFixedSize(captureSize.getWidth(), captureSize.getHeight());
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

	/**
	 * Gets the size from a camera that most closely matches an HD resolution with the aspect 320:240
	 * @param cc The camera characteristics
	 * @return The most optimal size (null if no sizes available at all)
	 */
	protected Size getCorrectSize(CameraCharacteristics cc) {
		int targetWidth = 320*6;
		int targetHeight = 240*6;
		int targetSize = targetHeight*targetWidth;
		Size current = null;
		StreamConfigurationMap scm = cc.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
		for (Size s : scm.getOutputSizes(ImageReader.class)) {
			if (current == null)
				current = s;
			else {
				int cS = current.getHeight()*current.getWidth() - targetSize;
				int sS = s.getHeight()*s.getWidth() - targetSize;
				if(Math.abs(cS) > Math.abs(sS)) {
					current = s;
				}
			}
		}
		return current;
	}

	/**
	 * Used to set the JPEG_ROTATION parameter for capture requests
	 * @return
	 */
	private int getJpegOrientation() {
		int deviceOrientation = activity.getWindowManager().getDefaultDisplay().getRotation();
		if (deviceOrientation == android.view.OrientationEventListener.ORIENTATION_UNKNOWN) return 0;

		// Round device orientation to a multiple of 90
		deviceOrientation = (deviceOrientation + 45) / 90 * 90;

		// Calculate desired JPEG orientation relative to camera orientation to make
		// the image upright relative to the device orientation
		int jpegOrientation = (cameraSensorOrientation + deviceOrientation + 360) % 360;

		return jpegOrientation;
	}




	private static class CameraStateCallback extends CameraDevice.StateCallback {

		ImageThread imageThread;

		public CameraStateCallback(ImageThread imgth) {
			imageThread = imgth;
		}

		public void onOpened(@NonNull final CameraDevice cameraDevice) {
			try {
				//Build ImageReader, CaptureRequest and CameraSession
				CaptureRequest.Builder builder = cameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_RECORD);
				imageThread.imageReader =  ImageReader.newInstance(imageThread.captureSize.getWidth(), imageThread.captureSize.getHeight(), ImageFormat.JPEG, 2);
				builder.addTarget(imageThread.imageReader.getSurface());
				builder.addTarget(imageThread.liveSurface);
				builder.set(CaptureRequest.CONTROL_MODE, CaptureRequest.CONTROL_MODE_AUTO); //all auto
				builder.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE); //Auto focus on
				builder.set(CaptureRequest.FLASH_MODE, CaptureRequest.FLASH_MODE_OFF); //Flash off
				builder.set(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_ON); //Exposure auto
				builder.set(CaptureRequest.CONTROL_AWB_MODE, CaptureRequest.CONTROL_AWB_MODE_AUTO); //WB auto
				builder.set(CaptureRequest.JPEG_ORIENTATION, imageThread.getJpegOrientation());
				builder.set(CaptureRequest.JPEG_QUALITY, (byte)95);
				imageThread.captureRequest = builder.build();
				cameraDevice.createCaptureSession(
					Arrays.asList(imageThread.imageReader.getSurface(), imageThread.liveSurface),
					new CameraSessionCallback(imageThread),
					imageThread.handler1);
			}
			catch (CameraAccessException e) {
				imageThread.cameraDisconnectAccessException();
			}
		}

		public void onDisconnected(@NonNull CameraDevice cameraDevice) {
			imageThread.cameraDisconnect("Camera disconnected", false);
		}

		public void onError(@NonNull CameraDevice cameraDevice, int i) {
			switch (i) {
				case CameraDevice.StateCallback.ERROR_CAMERA_IN_USE:
					imageThread.cameraDisconnect("Camera already in use", true);
					break;
				case CameraDevice.StateCallback.ERROR_MAX_CAMERAS_IN_USE:
					imageThread.cameraDisconnect("Max cameras in use", true);
					break;
				case CameraDevice.StateCallback.ERROR_CAMERA_DISABLED:
					imageThread.cameraDisconnect("Camera is disabled", true);
					break;
				case CameraDevice.StateCallback.ERROR_CAMERA_DEVICE:
					imageThread.cameraDisconnect("Camera error", true);
					break;
				case CameraDevice.StateCallback.ERROR_CAMERA_SERVICE:
					imageThread.cameraDisconnect("Camera service error", true);
					break;
				default:
					imageThread.cameraDisconnect("Unknown camera error", true);
					break;
			}
		}
	}

	private static class CameraSessionCallback extends CameraCaptureSession.StateCallback {

		ImageThread imageThread;
		byte[] bufferImage;
		Runnable process;

		public CameraSessionCallback(ImageThread imgth) {
			imageThread = imgth;
			final CameraSessionCallback csc = this;
			process = new Runnable() {
				@Override
				public void run() {
					if (csc.bufferImage == null)
						return;
					byte[] img = csc.bufferImage;
					csc.bufferImage = null;
					Bitmap bmp = imageThread.processor.process(img);
					if (bmp != null)
						imageThread.activity.setSignImage(bmp);
				}
			};
		}

		@Override
		public void onConfigured(@NonNull CameraCaptureSession cameraCaptureSession) {
			imageThread.cameraSession = cameraCaptureSession;
			if(imageThread.shouldStop || imageThread.cameraSession == null || imageThread.imageReader == null) {
				imageThread.stop();
				return;
			}
			try {
				imageThread.imageReader.setOnImageAvailableListener(new ImageReader.OnImageAvailableListener() {
					@Override
					public void onImageAvailable(ImageReader imageReader) {
						if(imageThread.shouldStop)
							return;
						Image img = imageReader.acquireLatestImage();
						if (imageThread.processor.checkReady() && img != null) {
							ByteBuffer buf = img.getPlanes()[0].getBuffer();
							byte[] bb = new byte[buf.remaining()];
							buf.get(bb);
							img.close();
							bufferImage = bb;
							if (imageThread.shouldStop)
								return;
							imageThread.handler2.post(process);
						}
					}
				}, imageThread.handler1);
				imageThread.cameraSession.setRepeatingRequest(imageThread.captureRequest, null, imageThread.handler1);
			}
			catch (CameraAccessException e) {
				imageThread.cameraDisconnectAccessException();
			}
		}

		@Override
		public void onConfigureFailed(@NonNull CameraCaptureSession cameraCaptureSession) {
			imageThread.cameraDisconnect("Camera configuration failed", true);
		}
	}

}
