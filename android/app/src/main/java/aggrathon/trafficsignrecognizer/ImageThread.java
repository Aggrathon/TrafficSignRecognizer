package aggrathon.trafficsignrecognizer;


import android.content.Context;
import android.graphics.ImageFormat;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.media.ImageReader;
import android.support.annotation.NonNull;
import android.util.Log;
import android.util.Size;
import android.widget.ImageView;

import java.util.Arrays;

public class ImageThread extends Thread {

	private boolean shouldStop;
	private ImageView imageView;
	private ImageReader imageReader;
	private CaptureRequest captureRequest;
	private CameraCaptureSession cameraSession;

	public void stopThread() {
		shouldStop = true;
		if(cameraSession != null)
			cameraSession.close();
	}

	public ImageThread(ImageView imageView) {
		shouldStop = false;
		this.imageView = imageView;
		//Create Camera binding
		final CameraManager manager = (CameraManager)imageView.getContext().getSystemService(Context.CAMERA_SERVICE);
		try {
			//Find the right camera and characteristics
			final String cameraId = getCorrectCamera(manager);
			if (cameraId == null) {
				Log.e("camera", "No suitable camera found");
				stopThread();
				return;
			}
			final CameraCharacteristics characteristics = manager.getCameraCharacteristics(cameraId);
			final Size captureSize = getCorrectSize(characteristics);
			if (captureSize == null) {
				Log.e("camera", "No suitable camera size found");
				stopThread();
				return;
			}
			//Open the camera
			manager.openCamera(cameraId, new CameraDevice.StateCallback() {
				@Override
				public void onOpened(@NonNull final CameraDevice cameraDevice) {
					try {
						//Build ImageReader, CaptureRequest and CameraSession
						CaptureRequest.Builder builder = cameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
						imageReader =  ImageReader.newInstance(captureSize.getWidth(), captureSize.getHeight(), ImageFormat.JPEG, 2);
						builder.addTarget(imageReader.getSurface());
						builder.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE); //Auto focus on
						builder.set(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_OFF); //Flash off
						captureRequest = builder.build();
						cameraDevice.createCaptureSession(Arrays.asList(imageReader.getSurface()), new CameraCaptureSession.StateCallback() {
							@Override
							public void onConfigured(@NonNull CameraCaptureSession cameraCaptureSession) {
								if (cameraDevice == null) {
									stopThread();
									return;
								}
								//TODO start capturing images
								cameraSession = cameraCaptureSession;
								start();
							}

							@Override
							public void onConfigureFailed(@NonNull CameraCaptureSession cameraCaptureSession) {
								Log.e("camera", "Camera configuration failed");
								stopThread();
							}
						}, null);
					}
					catch (CameraAccessException e) {
						Log.e("camera", "Access to the camera denied");
					}
				}

				@Override
				public void onDisconnected(@NonNull CameraDevice cameraDevice) {
					Log.d("camera", "Camera disconnected");
					stopThread();
				}

				@Override
				public void onError(@NonNull CameraDevice cameraDevice, int i) {
					switch (i) {
						case CameraDevice.StateCallback.ERROR_CAMERA_IN_USE:
							Log.e("camera", "Camera already in use");
							break;
						case CameraDevice.StateCallback.ERROR_MAX_CAMERAS_IN_USE:
							Log.e("camera", "Max cameras in use");
							break;
						case CameraDevice.StateCallback.ERROR_CAMERA_DISABLED:
							Log.e("camera", "Camera is disabled");
							break;
						case CameraDevice.StateCallback.ERROR_CAMERA_DEVICE:
							Log.e("camera", "Camera error");
							break;
						case CameraDevice.StateCallback.ERROR_CAMERA_SERVICE:
							Log.e("camera", "Camera service error");
							break;
						default:
							Log.e("camera", "Unknown camera error");
							break;
					}
					stopThread();
				}
			}, null);
		}
		catch (SecurityException e) {
			Log.e("camera", "Access to the camera not granted");
		}
		catch (CameraAccessException e) {
			Log.e("camera", "Access to the camera denied");
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
		int targetWidth = 320*4;
		int targetHeigth = 240*4;
		Size current = null;
		StreamConfigurationMap scm = cc.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
		for (Size s : scm.getOutputSizes(ImageReader.class)) {
			if (current == null)
				current = s;
			else {
				if (current.getHeight()*current.getWidth() < s.getHeight()*s.getWidth()) {
					if (current.getHeight() < targetHeigth || current.getWidth() < targetWidth)
						current = s;
				}
				else {
					if (s.getHeight() >= targetHeigth && s.getWidth() >= targetWidth)
						current = s;
				}
			}
		}
		return current;
	}

	@Override
	public void run() {
		while (!shouldStop) {
			//TODO Image recognition
			//Get Image From Camera
			//Run the image through the nn
			//Possibly Update the sign view
		}
		if(cameraSession != null) {
			cameraSession.close();
			cameraSession = null;
		}
		captureRequest = null;
		if (imageReader != null) {
			imageReader.close();
			imageReader = null;
		}
	}
}
