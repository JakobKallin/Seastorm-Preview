package com.seattletestbed;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ComponentName;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.content.pm.ResolveInfo;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;

import com.googlecode.android_scripting.FeaturedInterpreters;
import com.googlecode.android_scripting.interpreter.InterpreterConstants;

import java.net.URL;
import java.util.List;

/***
 * 
 * Based on the DialogActivity class found in the ScriptForAndroidTemplate package in SL4A
 * Only minor modifications were made to it
 *
 */
public class DialogActivity extends Activity {

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);

		String interpreter = FeaturedInterpreters.getInterpreterNameForScript("foo.py");

		if (interpreter == null) {
			Log.e(Common.LOG_TAG, Common.LOG_EXCEPTION_NO_PYTHON_INTERPRETER);
			finish();
		}

		final Intent activityIntent = new Intent();

		Intent resolveIntent = new Intent(InterpreterConstants.ACTION_DISCOVER_INTERPRETERS);
		resolveIntent.addCategory(Intent.CATEGORY_LAUNCHER);
		resolveIntent.setType(InterpreterConstants.MIME + ".py");
		List<ResolveInfo> resolveInfos = getPackageManager().queryIntentActivities(resolveIntent, 0);

		if (resolveInfos != null && resolveInfos.size() == 1) {
			ActivityInfo info = resolveInfos.get(0).activityInfo;
			activityIntent.setComponent(new ComponentName(info.packageName, info.name));
			activityIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
		} else {
			final URL url = FeaturedInterpreters.getUrlForName(interpreter);
			activityIntent.setAction(Intent.ACTION_VIEW);
			activityIntent.setData(Uri.parse(url.toString()));
		}

		AlertDialog.Builder dialog = new AlertDialog.Builder(this);
		dialog.setTitle(String.format("%s is not installed.", interpreter));
		dialog.setMessage(String.format("Do you want to download the installer APK for %s ?   You will need to download the installer, open it, and then click install before continuing to install Seattle.\nNote: If you do not see the installer downloading and extracting zip files, it has not completed!", interpreter));

		DialogInterface.OnClickListener buttonListener = new DialogInterface.OnClickListener() {
			@Override
			public void onClick(DialogInterface dialog, int which) {
				if (which == DialogInterface.BUTTON_POSITIVE) {
					Log.i(Common.LOG_TAG, Common.LOG_INFO_DOWNLOADING_PYTHON);
					startActivity(activityIntent);
				}
				dialog.dismiss();
				finish();
			}
		};
		dialog.setNegativeButton("No", buttonListener);
		dialog.setPositiveButton("Yes", buttonListener);
		dialog.show();
	}

}
