package com.seattletestbed.process;

import com.googlecode.android_scripting.AndroidProxy;
import com.googlecode.android_scripting.interpreter.InterpreterConfiguration;

import java.io.File;
import java.util.List;
import java.util.Map;

/***
 * 
 * Slightly modified version of the ScriptProcess from SL4A
 * with the possibility to launch scripts with
 * command-line arguments and environmental variables,
 * and to specify the working directory of the script at
 * launch time
 *
 */
public class SeattleScriptProcess extends PythonScriptProcess{

	public static SeattleScriptProcess launchScript(File script, InterpreterConfiguration configuration,
			final AndroidProxy proxy, Runnable shutdownHook, String workingDirectory, List<String> args, Map<String, String> environment) {
		if (!script.exists()) {
			throw new RuntimeException("No such script to launch.");
		}
		SeattleScriptProcess process = new SeattleScriptProcess(script, configuration, proxy, workingDirectory);
		if(environment != null)
			process.putAllEnvironmentVariables(environment);
		if (shutdownHook == null) {
			process.start(new Runnable() {
				@Override
				public void run() {
					proxy.shutdown();
				}
			}, args);
		} else {
			process.start(shutdownHook, args);
		}
		return process;
	}
	
	private String workingDirectory;

	private SeattleScriptProcess(File script,
			InterpreterConfiguration configuration, AndroidProxy proxy, String workingDirectory) {
		super(script, configuration, proxy);
		this.workingDirectory = workingDirectory;
	}

	@Override
	public String getWorkingDirectory() {
	   return workingDirectory;
	}
}
