package aggrathon.trafficsignrecognizer;

import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Build;
import android.support.annotation.NonNull;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.widget.ImageView;
import android.widget.Toast;

public class MainActivity extends AppCompatActivity {

	protected final static int PERMISSION_REQUEST_CODE_CAMERA = 234;

	protected ImageThread thread;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_main);
		requestCameraPermission();
	}

	@Override
	protected void onResume() {
		super.onResume();
		if (checkPermission())
			startThread();
	}

	protected void startThread() {
		if (thread != null)
			thread.stop();
		thread = new ImageThread((ImageView)findViewById(R.id.imageView), this);
	}

	@Override
	protected void onPause() {
		if (thread != null) {
			thread.stop();
			thread = null;
		}
		super.onPause();
	}

	protected boolean checkPermission() {
		if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M)
			return checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED;
		return true;
	}

	protected void requestCameraPermission() {
		if (!checkPermission() && Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
			if (shouldShowRequestPermissionRationale(Manifest.permission.CAMERA))
				Toast.makeText(this, "Camera needed for traffic sign recognition", Toast.LENGTH_LONG).show();
			requestPermissions(new String[] { Manifest.permission.CAMERA }, PERMISSION_REQUEST_CODE_CAMERA);
		}
	}

	@Override
	public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
		if (requestCode == PERMISSION_REQUEST_CODE_CAMERA) {
			if (permissions.length == 1 && permissions[0].equals(Manifest.permission.CAMERA)) {
				if(grantResults[0] != PackageManager.PERMISSION_GRANTED)
					requestCameraPermission();
				else
					startThread();
				return;
			}
		}
		super.onRequestPermissionsResult(requestCode, permissions, grantResults);
	}
}
