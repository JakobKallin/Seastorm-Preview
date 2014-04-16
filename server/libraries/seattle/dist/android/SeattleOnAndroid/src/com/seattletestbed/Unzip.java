package com.seattletestbed;

import android.util.Log;
import com.seattletestbed.R;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.util.Enumeration;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

/***
 * 
 * Utility class
 * 
 * Extracts a zip archive
 * 
 * Based on the code from "reakinator" @ http://stackoverflow.com/questions/5028421/android-unzip-a-folder
 *
 */
public class Unzip {

	private static final int BUFFER_SIZE = 8192;

	// Unzips a zip archive specified by filePath to the directory specified by destinationPath
	public static void unzip(String filePath, String destinationPath) throws Exception {

		// Create buffer to be used during the extraction process
		byte[] buffer = new byte[BUFFER_SIZE];

		// Get archive file
		File archive = new File(filePath);

		// Iterate through entries
		try {
			ZipFile zipfile = new ZipFile(archive);
			for (Enumeration<? extends ZipEntry> e = zipfile.entries(); e.hasMoreElements();) {
				ZipEntry entry = e.nextElement();
				// Unzip entry
				unzipEntry(zipfile, entry, destinationPath, buffer);
			}
		} catch (Exception e) {
			// Error occured
			Log.e(Common.LOG_TAG, Common.LOG_EXCEPTION_UNZIPPING_ARCHIVE + archive, e);
			throw e;
		}
	}
	
	// Unzips a zipEntry from the zipFile to the outputDir using the buffer specified in the arguments
	private static void unzipEntry(ZipFile zipFile, ZipEntry entry, String outputDir, byte[] buffer) throws Exception {
		
		// Check if the entry is a directory
		if (entry.isDirectory()) {
			// Create the directory (incl. complete directory path if necessary)
			(new File(outputDir, entry.getName())).mkdirs();
			return;
		}

		// Get output file
		File outputFile = new File(outputDir, entry.getName());
		
		// Create directory path if necessary
		if (!outputFile.getParentFile().exists()) {
			outputFile.getParentFile().mkdirs();
		}

		Log.v(Common.LOG_TAG, Common.LOG_VERBOSE_EXTRACTING_FILE + entry);

		// Set up input and output streams
		BufferedInputStream inputStream = new BufferedInputStream(zipFile.getInputStream(entry), buffer.length);
		BufferedOutputStream outputStream = new BufferedOutputStream(new FileOutputStream(outputFile), buffer.length);

		try {
			// Copy from input stream to output stream
			int readBytes;
			while((readBytes = inputStream.read(buffer))!=-1)
				outputStream.write(buffer, 0, readBytes);
		} catch (Exception e) {
			Log.e(Common.LOG_TAG, Common.LOG_EXCEPTION_UNZIPPING_FILE + entry, e);
		}
		finally {
			// Close streams
			outputStream.close();
			inputStream.close();
		}
	}
}
