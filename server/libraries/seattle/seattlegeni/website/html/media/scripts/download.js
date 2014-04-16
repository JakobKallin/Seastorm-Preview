$(document).ready(function() {
	detectOs();
});

function detectOs() {
	var os;
	if ((navigator.userAgent.match(/(android)/i))) {
		os = "Android";
	} else {
		os = $.browser.OS();
	}
	switch (os) {
		case "Windows":
			$("#downloads").prepend($("#win"));
			break;
		case "Mac":
			$("#downloads").prepend($("#mac"));
			break;
		case "Linux":
			$("#downloads").prepend($("#linux"));
			break;
		case "Android":
			$("#downloads").prepend($("#android"));
			break;
		default:
			break;
	}
}
